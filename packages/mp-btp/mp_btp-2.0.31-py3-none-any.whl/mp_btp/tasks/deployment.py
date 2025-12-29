import time
import random
import logging
import tempfile
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from mp_btp.models.database import SessionLocal
from mp_btp.models import Deployment, DeploymentReplica, Account, KymaRuntime, CFOrg
from mp_btp.integrations.kyma import download_kubeconfig, kyma_deploy, kyma_deploy_raw_yaml, kyma_login, check_deployment_ready, get_service_url
from mp_btp.integrations.cf import cf_login, cf_target, cf_push
from mp_btp.integrations.btp_cli import BTPClient
from mp_btp.config import get_config
logger = logging.getLogger(__name__)
config = get_config()
def get_multi_node_client():
    from mp_btp.integrations.proxy_pool import get_proxy_pool
    pool = get_proxy_pool()
    if not pool:
        return None
    return pool.get_proxy_for_account(account)
def wait_for_kyma_ready(account: Account, runtime: KymaRuntime, db: Session, timeout: int = 1800) -> bool:
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            logger.error(f"Deployment {deployment_id} not found")
            return
        delay_config = config.get("deployment", {}).get("delay", {})
        delay = random.randint(delay_config.get("single_min", 5), delay_config.get("single_max", 30))
        logger.info(f"Deployment {deployment_id}: waiting {delay}s")
        time.sleep(delay)
        mock_mode = config.get("deployment", {}).get("mock", True)
        use_multi_node = config.get("deployment", {}).get("use_multi_node", False)
        success_count = 0
        for replica in deployment.replicas_list:
            try:
                if mock_mode:
                    execute_replica_mock(db, deployment, replica)
                elif use_multi_node:
                    execute_replica_multi_node(db, deployment, replica)
                elif replica.runtime_type == "kyma":
                    execute_replica_kyma(db, deployment, replica)
                else:
                    execute_replica_cf(db, deployment, replica)
                success_count += 1
            except Exception as e:
                logger.error(f"Replica {replica.replica_index} failed: {e}")
                replica.status = "FAILED"
                db.commit()
        deployment.status = "RUNNING" if success_count > 0 else "FAILED"
        db.commit()
        logger.info(f"Deployment {deployment_id}: {success_count}/{len(deployment.replicas_list)} replicas")
    finally:
        db.close()
def execute_replica_mock(db: Session, deployment: Deployment, replica: DeploymentReplica):
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
    if not account or not runtime:
        raise Exception("Account or runtime not found")
    proxy = get_proxy_for_account(account)
    if proxy:
        logger.info(f"Using proxy {proxy.host}:{proxy.port} for {account.subdomain}")
    if runtime.status == "CREATING":
        logger.info(f"Waiting for Kyma {runtime.cluster_name} to be ready...")
        if not wait_for_kyma_ready(account, runtime, db, timeout=1800):
            raise Exception("Kyma creation timeout or failed")
        db.refresh(runtime)
    if not runtime.instance_id:
        raise Exception("Kyma instance_id not available")
    fd, kubeconfig_path = tempfile.mkstemp(suffix='.yaml')
    os.close(fd)
    try:
        if not download_kubeconfig(runtime.instance_id, kubeconfig_path):
            raise Exception("Failed to download kubeconfig")
        if not kyma_login(kubeconfig_path, account.email, account.password, port=8000):
            raise Exception("Kyma login failed")
        if deployment.raw_yaml:
            result = kyma_deploy_raw_yaml(kubeconfig_path, deployment.raw_yaml, namespace="demo")
            if not result['success']:
                raise Exception(f"Deploy failed: {result.get('error')}")
            url = f"https://{deployment.project}.{runtime.cluster_name or 'kyma'}.ondemand.com"
        else:
            result = kyma_deploy(kubeconfig_path, replica.container_name, deployment.image,
                                port=deployment.port, memory_mb=deployment.memory_mb,
                                env_vars=deployment.env_vars)
            if not result['success']:
                raise Exception(f"Deploy failed: {result.get('error')}")
            check_deployment_ready(kubeconfig_path, replica.container_name, timeout=180)
            url = get_service_url(kubeconfig_path, replica.container_name) or result.get('url')
        replica.status = "RUNNING"
        replica.access_url = url
        replica.started_at = datetime.now(timezone.utc)
        runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
        db.commit()
    finally:
        if os.path.exists(kubeconfig_path):
            os.unlink(kubeconfig_path)
def execute_replica_cf(db: Session, deployment: Deployment, replica: DeploymentReplica):
    client = get_multi_node_client()
    if not client:
        raise Exception("Multi-node API not configured")
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    if not account:
        raise Exception("Account not found")
    node_id = account.preferred_node
    if node_id:
        node = client.get_node(node_id)
        if not node or node.get("status") != "online":
            node_id = None
    if not node_id:
        nodes = client.list_nodes()
        online_nodes = [n for n in nodes if n.get("status") == "online"]
        if not online_nodes:
            raise Exception("No online nodes")
        node_id = random.choice(online_nodes).get("id")
        account.preferred_node = node_id
        db.commit()
        logger.info(f"Account {account.subdomain} bound to node {node_id}")
    replica.assigned_node = node_id
    if replica.runtime_type == "kyma":
        execute_kyma_on_node(client, node_id, db, deployment, replica, account)
    else:
        execute_cf_on_node(client, node_id, db, deployment, replica, account)
def execute_kyma_on_node(client, node_id: str, db: Session, deployment: Deployment, 
                         replica: DeploymentReplica, account: Account):
curl -s '{kubeconfig_url}' > /tmp/kubeconfig-{replica.container_name}.yaml
export KUBECONFIG=/tmp/kubeconfig-{replica.container_name}.yaml
kubectl apply -f - <<'EOF'
{manifest}
EOF
kubectl rollout status deployment/{replica.container_name} --timeout=180s
kubectl get svc {replica.container_name} -o jsonpath='{{.spec.clusterIP}}:{{.spec.ports[0].port}}'
    runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
    if not runtime:
        raise Exception("CF org not found")
    api = runtime.api_endpoint
    if not api:
        raise Exception("CF api_endpoint not configured")
    result = client.cf_login(node_id, api, account.email, account.password, org=runtime.org_name)
    if not result.get("success"):
        raise Exception(f"CF login failed: {result}")
    result = client.exec_on_node(node_id, cmd, timeout_ms=300000)
    if not result.get("success"):
        raise Exception(f"CF push failed: {result}")
    output = result.get("output", "")
    url = None
    for line in output.strip().split('\n'):
        if '.hana.ondemand.com' in line or '.cfapps.' in line:
            url = f"https://{line.strip()}"
            break
    replica.status = "RUNNING"
    replica.access_url = url
    replica.started_at = datetime.now(timezone.utc)
    runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
    db.commit()
    logger.info(f"Deployed {deployment.image} to CF via node {node_id}")
def build_k8s_manifest(name: str, image: str, port: int, memory_mb: int, env_vars: dict) -> str: