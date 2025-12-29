"""Cleanup tasks for deployments."""
import logging
import tempfile
import os
from sqlalchemy.orm import Session
from mp_btp.models import DeploymentReplica, Account, KymaRuntime, CFOrg
from mp_btp.integrations.kyma import download_kubeconfig, kyma_delete, kyma_login
from mp_btp.integrations.cf import cf_login, cf_delete

logger = logging.getLogger(__name__)


def cleanup_replica(db: Session, replica: DeploymentReplica) -> bool:
    """Delete actual resources for a replica."""
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    if not account:
        return False
    
    if replica.runtime_type == "kyma":
        return cleanup_kyma_replica(db, replica, account)
    else:
        return cleanup_cf_replica(db, replica, account)


def cleanup_kyma_replica(db: Session, replica: DeploymentReplica, account: Account) -> bool:
    """Delete Kyma deployment."""
    runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
    if not runtime or not runtime.instance_id:
        return False
    
    fd, kubeconfig_path = tempfile.mkstemp(suffix='.yaml')
    os.close(fd)
    
    try:
        if not download_kubeconfig(runtime.instance_id, kubeconfig_path):
            return False
        
        if not kyma_login(kubeconfig_path, account.email, account.password):
            return False
        
        if kyma_delete(kubeconfig_path, replica.container_name):
            logger.info(f"Deleted Kyma deployment: {replica.container_name}")
            return True
        return False
    finally:
        if os.path.exists(kubeconfig_path):
            os.unlink(kubeconfig_path)


def cleanup_cf_replica(db: Session, replica: DeploymentReplica, account: Account) -> bool:
    """Delete CF app."""
    runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
    if not runtime:
        return False
    
    api = runtime.api_endpoint
    if not api:
        logger.error("CF api_endpoint not configured")
        return False
    
    if not cf_login(api, account.email, account.password, org=runtime.org_name):
        return False
    
    if cf_delete(replica.container_name):
        logger.info(f"Deleted CF app: {replica.container_name}")
        return True
    return False
