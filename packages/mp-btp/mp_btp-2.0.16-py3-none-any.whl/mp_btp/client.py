#!/usr/bin/env python3
"""
BTP Scheduler Python SDK
Single-file client, copy and use directly.

Usage:
    from client import BTPScheduler
    
    client = BTPScheduler("http://localhost:8000")
    
    # Deploy to Kyma
    dep = client.deploy("nginx:alpine", env_type="kyma", memory_mb=256, port=80)
    print(dep["deployment_id"])
    
    # Wait for ready
    result = client.wait_ready(dep["deployment_id"])
    print(result["replicas"][0]["access_url"])
    
    # Delete
    client.delete(dep["deployment_id"])
"""
import requests
import time
from typing import Optional, Dict, List


class BTPScheduler:
    """BTP Scheduler API client."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v1{path}"
    
    def _get(self, path: str) -> Dict:
        r = requests.get(self._url(path), timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    
    def _post(self, path: str, data: Dict = None) -> Dict:
        r = requests.post(self._url(path), json=data, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    
    def _delete(self, path: str) -> Dict:
        r = requests.delete(self._url(path), timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    
    # Deployments
    def deploy(self, image: str, env_type: str = "kyma", replicas: int = 1,
               memory_mb: int = 256, port: int = None, env_vars: Dict = None,
               name: str = None, project: str = "default", expires_in_days: int = 0) -> Dict:
        """Create deployment."""
        data = {
            "image": image,
            "env_type": env_type,
            "replicas": replicas,
            "memory_mb": memory_mb,
            "project": project
        }
        if name:
            data["name"] = name
        if port:
            data["port"] = port
        if env_vars:
            data["env_vars"] = env_vars
        if expires_in_days:
            data["expires_in_days"] = expires_in_days
        return self._post("/deployments", data)
    
    def get(self, deployment_id: str) -> Dict:
        """Get deployment status."""
        return self._get(f"/deployments/{deployment_id}")
    
    def list(self, status: str = None, project: str = None) -> List[Dict]:
        """List deployments."""
        params = []
        if status:
            params.append(f"status={status}")
        if project:
            params.append(f"project={project}")
        path = "/deployments"
        if params:
            path += "?" + "&".join(params)
        return self._get(path)
    
    def delete(self, deployment_id: str) -> Dict:
        """Delete deployment."""
        return self._delete(f"/deployments/{deployment_id}")
    
    def wait_ready(self, deployment_id: str, timeout: int = 1800, interval: int = 10) -> Dict:
        """Wait for deployment to be RUNNING or FAILED."""
        start = time.time()
        while time.time() - start < timeout:
            dep = self.get(deployment_id)
            if dep["status"] in ["RUNNING", "FAILED"]:
                return dep
            time.sleep(interval)
        raise TimeoutError(f"Deployment {deployment_id} not ready after {timeout}s")
    
    # Accounts
    def accounts(self) -> List[Dict]:
        """List accounts."""
        return self._get("/accounts")
    
    def verify_account(self, account_id: str) -> Dict:
        """Verify account and sync resources."""
        return self._post(f"/accounts/{account_id}/verify")
    
    def account_runtimes(self, account_id: str) -> Dict:
        """Get account runtimes."""
        return self._get(f"/accounts/{account_id}/runtimes")
    
    # Kyma
    def kyma_pool(self) -> Dict:
        """Get Kyma pool status."""
        return self._get("/kyma/pool")
    
    def kyma_list(self, status: str = None) -> List[Dict]:
        """List Kyma runtimes."""
        path = "/kyma"
        if status:
            path += f"?status={status}"
        return self._get(path)
    
    def kyma_recreate(self, runtime_id: str) -> Dict:
        """Trigger Kyma recreation."""
        return self._post(f"/kyma/{runtime_id}/recreate")
    
    # Maintenance
    def stats(self) -> Dict:
        """Get system stats."""
        return self._get("/maintenance/stats")
    
    def trigger_cleanup(self) -> Dict:
        """Trigger cleanup task."""
        return self._post("/maintenance/cleanup")
    
    def trigger_cf_check(self) -> Dict:
        """Trigger CF daily check."""
        return self._post("/maintenance/cf-daily-check")


# CLI usage
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("Usage: python client.py <url> <command> [args]")
        print("Commands: deploy, get, list, delete, accounts, stats")
        print("Example: python client.py http://localhost:8000 deploy nginx:alpine")
        sys.exit(1)
    
    client = BTPScheduler(sys.argv[1])
    cmd = sys.argv[2]
    
    if cmd == "deploy":
        image = sys.argv[3] if len(sys.argv) > 3 else "nginx:alpine"
        r = client.deploy(image)
        print(json.dumps(r, indent=2))
    elif cmd == "get":
        r = client.get(sys.argv[3])
        print(json.dumps(r, indent=2))
    elif cmd == "list":
        r = client.list()
        print(json.dumps(r, indent=2))
    elif cmd == "delete":
        r = client.delete(sys.argv[3])
        print(json.dumps(r, indent=2))
    elif cmd == "accounts":
        r = client.accounts()
        print(json.dumps(r, indent=2))
    elif cmd == "stats":
        r = client.stats()
        print(json.dumps(r, indent=2))
    else:
        print(f"Unknown command: {cmd}")
