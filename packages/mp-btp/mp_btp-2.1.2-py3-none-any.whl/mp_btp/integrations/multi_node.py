#!/usr/bin/env python3
"""
Multi-Node API client for distributed command execution.
Single-file module, copy and use directly.

Usage:
    from multi_node import MultiNodeClient
    
    client = MultiNodeClient("http://node-api:8080")
    
    # Get available nodes
    nodes = client.list_nodes()
    
    # Execute on specific node
    result = client.exec_on_node("node-1", "whoami")
    
    # Batch execute on multiple nodes
    results = client.batch_exec("btp login ...", nodes=["node-1", "node-2"])
    
    # Batch execute by tags
    results = client.batch_exec("cf push ...", tags=["us", "asia"])
"""
import requests
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MultiNodeClient:
    """Client for multi-node API."""
    
    def __init__(self, base_url: str, token: str = None, timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v1{path}"
    
    def _get(self, path: str, params: Dict = None) -> Dict:
        r = requests.get(self._url(path), headers=self.headers, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    
    def _post(self, path: str, data: Dict = None) -> Dict:
        r = requests.post(self._url(path), headers=self.headers, json=data, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
    
    # Node operations
    def list_nodes(self, tags: List[str] = None) -> List[Dict]:
        """List available nodes."""
        params = {}
        if tags:
            params["tags"] = ",".join(tags)
        resp = self._get("/nodes", params)
        return resp.get("data", []) if resp.get("success") else []
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node details."""
        resp = self._get(f"/nodes/{node_id}")
        return resp.get("data") if resp.get("success") else None
    
    def exec_on_node(self, node_id: str, command: str, timeout_ms: int = 30000) -> Dict:
        """Execute command on single node."""
        resp = self._post(f"/nodes/{node_id}/exec", {
            "command": command,
            "timeout": timeout_ms
        })
        return resp
    
    # Batch operations
    def batch_exec(self, command: str, nodes: List[str] = None, tags: List[str] = None,
                   async_mode: bool = False, timeout_ms: int = 60000, concurrency: int = 10) -> Dict:
        """
        Execute command on multiple nodes.
        
        Args:
            command: Command to execute
            nodes: List of node IDs (optional)
            tags: List of tags to filter nodes (optional)
            async_mode: If True, returns job_id immediately
            timeout_ms: Timeout per node in milliseconds
            concurrency: Max concurrent executions
        
        Returns:
            Sync mode: {"success": bool, "results": [...]}
            Async mode: {"success": bool, "job_id": str}
        """
        data = {
            "command": command,
            "targets": {},
            "options": {
                "async": async_mode,
                "timeout": timeout_ms,
                "concurrency": concurrency
            }
        }
        
        if nodes:
            data["targets"]["nodes"] = nodes
        if tags:
            data["targets"]["tags"] = tags
        
        return self._post("/batch/exec", data)
    
    def get_job(self, job_id: str) -> Dict:
        """Get async job status."""
        return self._get(f"/batch/jobs/{job_id}")
    
    def wait_job(self, job_id: str, timeout: int = 300, interval: int = 2) -> Dict:
        """Wait for async job to complete."""
        start = time.time()
        while time.time() - start < timeout:
            resp = self.get_job(job_id)
            if resp.get("success"):
                job = resp.get("job", {})
                if job.get("status") in ["completed", "failed"]:
                    return resp
            time.sleep(interval)
        raise TimeoutError(f"Job {job_id} not completed after {timeout}s")
    
    # Convenience methods for BTP operations
    def btp_login(self, node_id: str, subdomain: str, email: str, password: str) -> Dict:
        """Execute BTP login on node."""
        cmd = f"btp login --url https://cli.btp.cloud.sap/ --subdomain {subdomain} --user {email} --password '{password}'"
        return self.exec_on_node(node_id, cmd)
    
    def cf_login(self, node_id: str, api: str, email: str, password: str, org: str = None) -> Dict:
        """Execute CF login on node."""
        cmd = f"cf login -a {api} -u {email} -p '{password}'"
        if org:
            cmd += f" -o {org}"
        return self.exec_on_node(node_id, cmd)
    
    def cf_push(self, node_id: str, app_name: str, image: str, memory: str = "256M") -> Dict:
        """Execute CF push on node."""
        cmd = f"cf push {app_name} --docker-image {image} -m {memory}"
        return self.exec_on_node(node_id, cmd, timeout_ms=300000)
    
    def kubectl_apply(self, node_id: str, manifest: str, kubeconfig: str = None) -> Dict:
        """Execute kubectl apply on node."""
        cmd = f"kubectl apply -f - <<'EOF'\n{manifest}\nEOF"
        if kubeconfig:
            cmd = f"KUBECONFIG={kubeconfig} {cmd}"
        return self.exec_on_node(node_id, cmd)


def select_node_for_region(client: MultiNodeClient, region: str) -> Optional[str]:
    """Select a node for given region (us, eu, asia, etc.)."""
    nodes = client.list_nodes(tags=[region])
    if nodes:
        # Return first online node
        for node in nodes:
            if node.get("status") == "online":
                return node.get("id")
    return None


# CLI usage
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("Usage: python multi_node.py <api_url> <command> [args]")
        print("Commands: nodes, exec <node_id> <cmd>, batch <cmd>")
        sys.exit(1)
    
    client = MultiNodeClient(sys.argv[1])
    cmd = sys.argv[2]
    
    if cmd == "nodes":
        r = client.list_nodes()
        print(json.dumps(r, indent=2))
    elif cmd == "exec" and len(sys.argv) >= 5:
        r = client.exec_on_node(sys.argv[3], sys.argv[4])
        print(json.dumps(r, indent=2))
    elif cmd == "batch" and len(sys.argv) >= 4:
        r = client.batch_exec(sys.argv[3])
        print(json.dumps(r, indent=2))
    else:
        print(f"Unknown command or missing args: {cmd}")
