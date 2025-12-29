#!/usr/bin/env python3
"""
Quick shell access to CF apps and Kyma pods.

Usage:
    # CF SSH
    python shell.py cf <deployment_id> [replica_index]
    
    # Kyma exec
    python shell.py kyma <deployment_id> [replica_index]
    
    # Print connection commands only
    python shell.py info <deployment_id>
"""
import sys
import os
import subprocess

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mp_btp.models.database import SessionLocal
from mp_btp.models import Deployment, DeploymentReplica, Account, KymaRuntime, CFOrg
from mp_btp.integrations.cf import cf_login
from mp_btp.integrations.kyma import download_kubeconfig, kyma_login
import tempfile


def get_replica(deployment_id: str, replica_index: int = 0):
    """Get deployment replica info."""
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            print(f"Deployment {deployment_id} not found")
            return None
        
        replica = None
        for r in deployment.replicas_list:
            if r.replica_index == replica_index:
                replica = r
                break
        
        if not replica:
            print(f"Replica {replica_index} not found")
            return None
        
        account = db.query(Account).filter(Account.id == replica.account_id).first()
        
        if replica.runtime_type == "kyma":
            runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
        else:
            runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
        
        return {
            "deployment": deployment,
            "replica": replica,
            "account": account,
            "runtime": runtime
        }
    finally:
        db.close()


def cf_ssh(deployment_id: str, replica_index: int = 0):
    """SSH into CF app."""
    info = get_replica(deployment_id, replica_index)
    if not info:
        return
    
    replica = info["replica"]
    account = info["account"]
    runtime = info["runtime"]
    
    if replica.runtime_type != "cf":
        print("Not a CF deployment, use 'kyma' command")
        return
    
    api = runtime.api_endpoint
    if not api:
        print("CF api_endpoint not configured")
        return
    
    print(f"Logging in to CF as {account.email}...")
    if not cf_login(api, account.email, account.password, org=runtime.org_name):
        print("CF login failed")
        return
    
    # Target space
    subprocess.run(["cf", "target", "-s", "dev"], capture_output=True)
    
    print(f"Connecting to {replica.container_name}...")
    os.execvp("cf", ["cf", "ssh", replica.container_name])


def kyma_exec(deployment_id: str, replica_index: int = 0):
    """Exec into Kyma pod."""
    info = get_replica(deployment_id, replica_index)
    if not info:
        return
    
    replica = info["replica"]
    account = info["account"]
    runtime = info["runtime"]
    
    if replica.runtime_type != "kyma":
        print("Not a Kyma deployment, use 'cf' command")
        return
    
    if not runtime.instance_id:
        print("Kyma instance_id not available")
        return
    
    # Download kubeconfig
    fd, kubeconfig_path = tempfile.mkstemp(suffix='.yaml')
    os.close(fd)
    
    print(f"Downloading kubeconfig...")
    if not download_kubeconfig(runtime.instance_id, kubeconfig_path):
        print("Failed to download kubeconfig")
        return
    
    print(f"Logging in to Kyma as {account.email}...")
    if not kyma_login(kubeconfig_path, account.email, account.password):
        print("Kyma login failed")
        return
    
    # Get pod name
    os.environ["KUBECONFIG"] = kubeconfig_path
    result = subprocess.run(
        ["kubectl", "get", "pods", "-l", f"app={replica.container_name}", "-o", "jsonpath={.items[0].metadata.name}"],
        capture_output=True, text=True
    )
    
    if result.returncode != 0 or not result.stdout:
        print(f"Pod not found for {replica.container_name}")
        return
    
    pod_name = result.stdout.strip()
    print(f"Connecting to pod {pod_name}...")
    os.execvp("kubectl", ["kubectl", "exec", "-it", pod_name, "--", "/bin/sh"])


def show_info(deployment_id: str):
    """Show connection info for all replicas."""
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            print(f"Deployment {deployment_id} not found")
            return
        
        print(f"Deployment: {deployment.id}")
        print(f"Image: {deployment.image}")
        print(f"Status: {deployment.status}")
        print()
        
        for replica in deployment.replicas_list:
            account = db.query(Account).filter(Account.id == replica.account_id).first()
            
            print(f"Replica {replica.replica_index}:")
            print(f"  Container: {replica.container_name}")
            print(f"  Status: {replica.status}")
            print(f"  URL: {replica.access_url}")
            print(f"  Account: {account.email}")
            
            if replica.runtime_type == "cf":
                runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
                print(f"  Type: CF ({runtime.org_name})")
                print(f"  Command: python shell.py cf {deployment_id} {replica.replica_index}")
                print(f"  Manual:")
                print(f"    cf login -a {runtime.api_endpoint} -u {account.email}")
                print(f"    cf target -o {runtime.org_name} -s dev")
                print(f"    cf ssh {replica.container_name}")
            else:
                runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
                print(f"  Type: Kyma ({runtime.cluster_name})")
                print(f"  Command: python shell.py kyma {deployment_id} {replica.replica_index}")
                print(f"  Manual:")
                print(f"    # Download kubeconfig from: https://kyma-env-broker.cp.kyma.cloud.sap/kubeconfig/{runtime.instance_id}")
                print(f"    kubectl exec -it <pod> -- /bin/sh")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    deployment_id = sys.argv[2]
    replica_index = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    if cmd == "cf":
        cf_ssh(deployment_id, replica_index)
    elif cmd == "kyma":
        kyma_exec(deployment_id, replica_index)
    elif cmd == "info":
        show_info(deployment_id)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
