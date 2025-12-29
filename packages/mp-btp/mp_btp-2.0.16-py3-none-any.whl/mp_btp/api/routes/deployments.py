from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from models import get_db, Deployment, DeploymentReplica, Account, KymaRuntime
from api.schemas import DeploymentCreate, DeploymentResponse, ReplicaResponse
from mp_btp.scheduler.core import select_account_for_deployment, select_accounts_for_replicas
from mp_btp.tasks.deployment import execute_deployment

router = APIRouter(prefix="/deployments", tags=["deployments"])

@router.post("", response_model=DeploymentResponse)
def create_deployment(req: DeploymentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Select accounts for replicas
    if req.replicas == 1:
        account, runtime = select_account_for_deployment(db, req.env_type, req.memory_mb)
        if not account:
            raise HTTPException(503, "No available account")
        assignments = [(account, runtime)]
    else:
        assignments = select_accounts_for_replicas(db, req.env_type, req.memory_mb, req.replicas)
        if not assignments:
            raise HTTPException(503, "No available accounts for replicas")
    
    # Create deployment
    expires_at = datetime.now(timezone) + timedelta(days=req.expires_in_days) if req.expires_in_days > 0 else None
    deployment = Deployment(
        project=req.project, env_type=req.env_type, image=req.image,
        replicas=req.replicas, memory_mb=req.memory_mb, disk_mb=req.disk_mb,
        port=req.port, env_vars=req.env_vars, expires_at=expires_at
    )
    db.add(deployment)
    db.flush()
    
    # Create replicas
    image_name = req.image.split(':')[0].split('/')[-1]
    replicas = []
    for i, (account, runtime) in enumerate(assignments):
        replica = DeploymentReplica(
            deployment_id=deployment.id, replica_index=i,
            account_id=account.id, 
            runtime_id=runtime.id if runtime else None,
            runtime_type=req.env_type, 
            container_name=f"{image_name}-{deployment.id.hex[:8]}-{i}"
        )
        db.add(replica)
        replicas.append(replica)
    
    db.commit()
    db.refresh(deployment)
    
    # Execute in background
    background_tasks.add_task(execute_deployment, str(deployment.id))
    
    return DeploymentResponse(
        deployment_id=deployment.id, status=deployment.status, project=deployment.project,
        image=deployment.image, env_type=deployment.env_type, created_at=deployment.created_at,
        expires_at=deployment.expires_at,
        replicas=[ReplicaResponse(
            replica_index=r.replica_index, account_id=r.account_id, status=r.status
        ) for r in replicas]
    )

@router.get("", response_model=List[DeploymentResponse])
def list_deployments(status: Optional[str] = None, project: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Deployment)
    if status:
        query = query.filter(Deployment.status == status)
    if project:
        query = query.filter(Deployment.project == project)
    
    deployments = query.order_by(Deployment.created_at.desc()).limit(50).all()
    return [DeploymentResponse(
        deployment_id=d.id, status=d.status, project=d.project, image=d.image,
        env_type=d.env_type, created_at=d.created_at, expires_at=d.expires_at,
        replicas=[ReplicaResponse(
            replica_index=r.replica_index, account_id=r.account_id,
            status=r.status, access_url=r.access_url, started_at=r.started_at
        ) for r in d.replicas_list]
    ) for d in deployments]

@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: str, db: Session = Depends(get_db)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    
    return DeploymentResponse(
        deployment_id=deployment.id, status=deployment.status, project=deployment.project,
        image=deployment.image, env_type=deployment.env_type, created_at=deployment.created_at,
        expires_at=deployment.expires_at,
        replicas=[ReplicaResponse(
            replica_index=r.replica_index, account_id=r.account_id,
            status=r.status, access_url=r.access_url, started_at=r.started_at
        ) for r in deployment.replicas_list]
    )

@router.delete("/{deployment_id}")
def delete_deployment(deployment_id: str, db: Session = Depends(get_db)):
    from mp_btp.tasks.cleanup import cleanup_replica
    
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    
    # Actually delete resources
    for replica in deployment.replicas_list:
        if replica.status == "RUNNING":
            cleanup_replica(db, replica)
        replica.status = "STOPPED"
        replica.stopped_at = datetime.now(timezone)
    
    deployment.status = "STOPPED"
    db.commit()
    
    return {"message": "Deployment stopped", "deployment_id": deployment_id}

@router.patch("/{deployment_id}")
def update_deployment(deployment_id: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    
    if status and status in ["RUNNING", "STOPPED", "PENDING"]:
        deployment.status = status
        db.commit()
    
    return {"message": "Deployment updated"}


@router.get("/{deployment_id}/shell")
def get_shell_info(deployment_id: str, replica_index: int = 0, db: Session = Depends(get_db)):
    """Get shell/SSH connection info for a deployment replica."""
    from models import CFOrg
    
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    
    replica = None
    for r in deployment.replicas_list:
        if r.replica_index == replica_index:
            replica = r
            break
    
    if not replica:
        raise HTTPException(404, f"Replica {replica_index} not found")
    
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    
    if replica.runtime_type == "cf":
        runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
        return {
            "type": "cf",
            "container": replica.container_name,
            "account": account.email,
            "org": runtime.org_name,
            "api_endpoint": runtime.api_endpoint,
            "commands": [
                f"cf login -a {runtime.api_endpoint} -u {account.email} -p '<password>'",
                f"cf target -o {runtime.org_name} -s dev",
                f"cf ssh {replica.container_name}"
            ],
            "quick": f"python shell.py cf {deployment_id} {replica_index}"
        }
    else:
        runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
        kubeconfig_url = f"https://kyma-env-broker.cp.kyma.cloud.sap/kubeconfig/{runtime.instance_id}"
        return {
            "type": "kyma",
            "container": replica.container_name,
            "account": account.email,
            "cluster": runtime.cluster_name,
            "kubeconfig_url": kubeconfig_url,
            "commands": [
                f"curl -s '{kubeconfig_url}' > kubeconfig.yaml",
                f"export KUBECONFIG=kubeconfig.yaml",
                f"kubectl get pods -l app={replica.container_name}",
                f"kubectl exec -it <pod-name> -- /bin/sh"
            ],
            "quick": f"python shell.py kyma {deployment_id} {replica_index}"
        }
