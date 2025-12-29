import time
import random
import logging
import tempfile
import os
from datetime import datetime, UTC, timedelta
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models import Deployment, DeploymentReplica, Account, KymaRuntime, CFOrg
from integrations.kyma import download_kubeconfig, kyma_deploy, kyma_deploy_raw_yaml, kyma_login, check_deployment_ready, get_service_url
from integrations.cf import cf_login, cf_target, cf_push
from integrations.btp_cli import BTPClient
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()


def get_multi_node_client():
    """Get multi-node client if enabled."""
    mn_config = config.get("multi_node", {})
    if not mn_config.get("enabled"):
        return None
    
    url = os.environ.get("MULTI_NODE_API_URL") or mn_config.get("url")
    token = os.environ.get("MULTI_NODE_API_TOKEN") or mn_config.get("token")
    
    if not url:
        return None
    
    from integrations.multi_node import MultiNodeClient
    return MultiNodeClient(url, token=token, timeout=mn_config.get("timeout", 300))


def get_proxy_for_account(account):
    """Get proxy for account if proxy pool enabled."""
    from integrations.proxy_pool import get_proxy_pool
    pool = get_proxy_pool()
    if not pool:
        return None
    return pool.get_proxy_for_account(account)


def wait_for_kyma_ready(account: Account, runtime: KymaRuntime, db: Session, timeout: int = 1800) -> bool:
    """Wait for CREATING Kyma to become ready. Polls every 30 seconds."""
    start = time.time()
    client = BTPClient(account.subdomain, account.email, account.password)
    
    while time.time() - start < timeout:
        if not client.login():
            time.sleep(30)
            continue
        
        subaccount_id = account.subaccount_id or client.get_subaccount_id()
        if not subaccount_id:
            time.sleep(30)
            continue
        
        kyma = client.get_kyma_instance(subaccount_id)
        if kyma:
            state = kyma.get("state")
            if state == "OK":
                runtime.instance_id = kyma.get("id")
                runtime.cluster_name = kyma.get("name")
                runtime.status = "OK"
                runtime.expires_at = datetime.now(UTC) + timedelta(days=14)
                db.commit()
                logger.info(f"Kyma {runtime.cluster_name} is ready")
                return True
            elif state == "FAILED":
                runtime.status = "FAILED"
                runtime.failed_count = (runtime.failed_count or 0) + 1
                db.commit()
                logger.error(f"Kyma creation failed for {account.subdomain}")
                return False
        
        logger.info(f"Kyma still creating, waiting... ({int(time.time() - start)}s)")
        time.sleep(30)
    
    logger.error(f"Kyma creation timeout after {timeout}s")
    return False


def execute_deployment(deployment_id: str):
    """Execute deployment task in background."""
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
    """Mock deployment."""
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    if not account:
        raise Exception("Account not found")
    
    if replica.runtime_type == "kyma":
        runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
        url = f"https://{replica.container_name}.{runtime.cluster_name or 'kyma'}.ondemand.com"
    else:
        runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
        # Extract region from api_endpoint (e.g., api.cf.ap21.hana... -> ap21)
        region = "unknown"
        if runtime and runtime.api_endpoint:
            parts = runtime.api_endpoint.split('.')
            if len(parts) >= 3:
                region = parts[2]  # api.cf.{region}.hana...
        url = f"https://{replica.container_name}.cfapps.{region}.hana.ondemand.com"
    
    replica.status = "RUNNING"
    replica.access_url = url
    replica.started_at = datetime.now(UTC)
    if runtime:
        runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
    db.commit()


def execute_replica_kyma(db: Session, deployment: Deployment, replica: DeploymentReplica):
    """Real Kyma deployment. Waits for CREATING Kyma if needed."""
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
    
    if not account or not runtime:
        raise Exception("Account or runtime not found")
    
    # Get proxy for account (if proxy pool enabled)
    proxy = get_proxy_for_account(account)
    if proxy:
        logger.info(f"Using proxy {proxy.host}:{proxy.port} for {account.subdomain}")
    
    # Wait for CREATING Kyma to be ready (up to 30 min)
    if runtime.status == "CREATING":
        logger.info(f"Waiting for Kyma {runtime.cluster_name} to be ready...")
        if not wait_for_kyma_ready(account, runtime, db, timeout=1800):
            raise Exception("Kyma creation timeout or failed")
        # Refresh runtime from DB
        db.refresh(runtime)
    
    if not runtime.instance_id:
        raise Exception("Kyma instance_id not available")
    
    fd, kubeconfig_path = tempfile.mkstemp(suffix='.yaml')
    os.close(fd)
    
    try:
        if not download_kubeconfig(runtime.instance_id, kubeconfig_path):
            raise Exception("Failed to download kubeconfig")
        
        # Use port 8000 for Kyma login (required for OAuth redirect)
        if not kyma_login(kubeconfig_path, account.email, account.password, port=8000):
            raise Exception("Kyma login failed")
        
        # 如果是 raw_yaml 部署 (compose 或 k8s-yaml)
        if deployment.raw_yaml:
            result = kyma_deploy_raw_yaml(kubeconfig_path, deployment.raw_yaml, namespace="demo")
            if not result['success']:
                raise Exception(f"Deploy failed: {result.get('error')}")
            # raw_yaml 部署不检查单个 deployment，直接标记成功
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
        replica.started_at = datetime.now(UTC)
        runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
        db.commit()
    finally:
        if os.path.exists(kubeconfig_path):
            os.unlink(kubeconfig_path)


def execute_replica_cf(db: Session, deployment: Deployment, replica: DeploymentReplica):
    """Real CF deployment."""
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
    
    if not account or not runtime:
        raise Exception("Account or runtime not found")
    
    # Get proxy for account (if proxy pool enabled)
    proxy = get_proxy_for_account(account)
    if proxy:
        logger.info(f"Using proxy {proxy.host}:{proxy.port} for {account.subdomain}")
    
    api = runtime.api_endpoint
    if not api:
        raise Exception("CF api_endpoint not configured, run account verify first")
    
    if not cf_login(api, account.email, account.password, org=runtime.org_name):
        raise Exception("CF login failed")
    
    cf_target(runtime.org_name, "dev")
    
    result = cf_push(replica.container_name, deployment.image,
                    memory_mb=deployment.memory_mb,
                    disk_mb=deployment.disk_mb or deployment.memory_mb * 2,
                    env_vars=deployment.env_vars)
    
    if not result['success']:
        raise Exception(f"CF push failed: {result.get('error')}")
    
    replica.status = "RUNNING"
    replica.access_url = result.get('url')
    replica.started_at = datetime.now(UTC)
    runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
    db.commit()


def execute_replica_multi_node(db: Session, deployment: Deployment, replica: DeploymentReplica):
    """Execute deployment via multi-node API (distributed execution)."""
    client = get_multi_node_client()
    if not client:
        raise Exception("Multi-node API not configured")
    
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    if not account:
        raise Exception("Account not found")
    
    # Node affinity: prefer account's assigned node
    node_id = account.preferred_node
    
    if node_id:
        # Verify node is online
        node = client.get_node(node_id)
        if not node or node.get("status") != "online":
            node_id = None  # Fall back to selection
    
    if not node_id:
        # Select a node and bind to account
        nodes = client.list_nodes()
        online_nodes = [n for n in nodes if n.get("status") == "online"]
        if not online_nodes:
            raise Exception("No online nodes")
        
        node_id = random.choice(online_nodes).get("id")
        account.preferred_node = node_id  # Bind account to this node
        db.commit()
        logger.info(f"Account {account.subdomain} bound to node {node_id}")
    
    replica.assigned_node = node_id
    
    if replica.runtime_type == "kyma":
        execute_kyma_on_node(client, node_id, db, deployment, replica, account)
    else:
        execute_cf_on_node(client, node_id, db, deployment, replica, account)


def execute_kyma_on_node(client, node_id: str, db: Session, deployment: Deployment, 
                         replica: DeploymentReplica, account: Account):
    """Execute Kyma deployment on remote node."""
    runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
    if not runtime or not runtime.instance_id:
        raise Exception("Kyma runtime not found")
    
    # 1. BTP login
    result = client.btp_login(node_id, account.subdomain, account.email, account.password)
    if not result.get("success"):
        raise Exception(f"BTP login failed: {result}")
    
    # 2. Download kubeconfig and deploy
    kubeconfig_url = f"https://kyma-env-broker.cp.kyma.cloud.sap/kubeconfig/{runtime.instance_id}"
    
    # Build kubectl command
    manifest = build_k8s_manifest(replica.container_name, deployment.image, 
                                  deployment.port, deployment.memory_mb, deployment.env_vars)
    
    cmd = f"""
curl -s '{kubeconfig_url}' > /tmp/kubeconfig-{replica.container_name}.yaml
export KUBECONFIG=/tmp/kubeconfig-{replica.container_name}.yaml
kubectl apply -f - <<'EOF'
{manifest}
EOF
kubectl rollout status deployment/{replica.container_name} --timeout=180s
kubectl get svc {replica.container_name} -o jsonpath='{{.spec.clusterIP}}:{{.spec.ports[0].port}}'
"""
    
    result = client.exec_on_node(node_id, cmd, timeout_ms=300000)
    
    if not result.get("success"):
        raise Exception(f"Kyma deploy failed: {result}")
    
    # Parse output for URL
    output = result.get("output", "")
    url = None
    for line in output.strip().split('\n'):
        if ':' in line and not line.startswith('deployment') and not line.startswith('service'):
            url = f"http://{line.strip()}"
            break
    
    replica.status = "RUNNING"
    replica.access_url = url
    replica.started_at = datetime.now(UTC)
    runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
    db.commit()
    logger.info(f"Deployed {deployment.image} to Kyma via node {node_id}")


def execute_cf_on_node(client, node_id: str, db: Session, deployment: Deployment,
                       replica: DeploymentReplica, account: Account):
    """Execute CF deployment on remote node."""
    runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
    if not runtime:
        raise Exception("CF org not found")
    
    api = runtime.api_endpoint
    if not api:
        raise Exception("CF api_endpoint not configured")
    
    # 1. CF login
    result = client.cf_login(node_id, api, account.email, account.password, org=runtime.org_name)
    if not result.get("success"):
        raise Exception(f"CF login failed: {result}")
    
    # 2. Target space and push
    cmd = f"""
cf target -s dev 2>/dev/null || cf create-space dev && cf target -s dev
cf push {replica.container_name} --docker-image {deployment.image} -m {deployment.memory_mb}M -k {(deployment.disk_mb or deployment.memory_mb * 2)}M
cf app {replica.container_name} | grep routes | awk '{{print $2}}'
"""
    
    result = client.exec_on_node(node_id, cmd, timeout_ms=300000)
    
    if not result.get("success"):
        raise Exception(f"CF push failed: {result}")
    
    # Parse output for URL
    output = result.get("output", "")
    url = None
    for line in output.strip().split('\n'):
        if '.hana.ondemand.com' in line or '.cfapps.' in line:
            url = f"https://{line.strip()}"
            break
    
    replica.status = "RUNNING"
    replica.access_url = url
    replica.started_at = datetime.now(UTC)
    runtime.memory_used_mb = (runtime.memory_used_mb or 0) + deployment.memory_mb
    db.commit()
    logger.info(f"Deployed {deployment.image} to CF via node {node_id}")


def build_k8s_manifest(name: str, image: str, port: int, memory_mb: int, env_vars: dict) -> str:
    """Build Kubernetes manifest YAML."""
    import yaml
    
    dep = {
        'apiVersion': 'apps/v1', 'kind': 'Deployment',
        'metadata': {'name': name, 'namespace': 'default'},
        'spec': {
            'replicas': 1, 'selector': {'matchLabels': {'app': name}},
            'template': {
                'metadata': {'labels': {'app': name}},
                'spec': {'containers': [{
                    'name': 'app', 'image': image,
                    'resources': {'requests': {'memory': f'{memory_mb}Mi'}, 'limits': {'memory': f'{memory_mb}Mi'}}
                }]}
            }
        }
    }
    if port:
        dep['spec']['template']['spec']['containers'][0]['ports'] = [{'containerPort': port}]
    if env_vars:
        dep['spec']['template']['spec']['containers'][0]['env'] = [{'name': k, 'value': str(v)} for k, v in env_vars.items()]
    
    manifests = [dep]
    if port:
        manifests.append({
            'apiVersion': 'v1', 'kind': 'Service',
            'metadata': {'name': name, 'namespace': 'default'},
            'spec': {'selector': {'app': name}, 'ports': [{'port': port, 'targetPort': port}], 'type': 'ClusterIP'}
        })
    
    return '---\n'.join(yaml.dump(m) for m in manifests)
