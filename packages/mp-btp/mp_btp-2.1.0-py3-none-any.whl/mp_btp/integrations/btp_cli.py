#!/usr/bin/env python3
import subprocess
import re
import json
import os
import logging
from typing import Dict, List, Optional
logger = logging.getLogger(__name__)
class BTPClient:
    def __init__(self, subdomain: str, email: str, password: str,
                 url: str = "https://cli.btp.cloud.sap/", proxy_env: Dict = None):
        self.subdomain = subdomain
        self.email = email
        self.password = password
        self.url = url
        self.proxy_env = proxy_env or {}
    def _run(self, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env.update(self.proxy_env)
        return subprocess.run(["btp"] + args, capture_output=True, text=True, 
                            timeout=timeout, env=env)
    def login(self) -> bool:
        try:
            r = self._run(["login", "--url", self.url, "--subdomain", self.subdomain,
                          "--user", self.email, "--password", self.password])
            return r.returncode == 0
        except Exception as e:
            logger.error(f"BTP login failed: {e}")
            return False
    def get_subaccount_id(self) -> Optional[str]:
        try:
            r = self._run(["list", "accounts/subaccount"])
            if r.returncode != 0:
                return None
            base = self.subdomain.replace('-ga', '')
            for line in r.stdout.split('\n'):
                if base in line:
                    m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', line)
                    if m:
                        return m.group(1)
            return None
        except:
            return None
    def list_environment_instances(self, subaccount_id: str) -> List[Dict]:
        try:
            r = self._run(["list", "accounts/environment-instance", "-sa", subaccount_id])
            if r.returncode != 0:
                return []
            instances, in_data = [], False
            for line in r.stdout.split('\n'):
                if 'environment name' in line.lower():
                    in_data = True
                    continue
                if in_data and line.strip() and line.strip() != 'OK':
                    m = re.search(r'([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})', line)
                    if m:
                        parts = line[m.end():].strip().split()
                        env_type = parts[0] if parts else ""
                        state = parts[1] if len(parts) > 1 else ""
                        landscape = parts[-1] if len(parts) > 3 else ""
                        inst = {"id": m.group(1), "name": line[:m.start()].strip(),
                               "type": env_type, "state": state, "landscape": landscape}
                        if env_type == "cloudfoundry" and landscape:
                            inst["api_endpoint"] = f"https://api.cf.{landscape.replace('cf-', '')}.hana.ondemand.com"
                        instances.append(inst)
            return instances
        except:
            return []
    def get_subaccount_info(self, subaccount_id: str) -> Optional[Dict]:
        try:
            r = self._run(["get", "accounts/subaccount", subaccount_id])
            if r.returncode != 0:
                return None
            info = {}
            for line in r.stdout.split('\n'):
                if 'region' in line.lower():
                    m = re.search(r'region[:\s]+(\S+)', line, re.I)
                    if m:
                        info['region'] = m.group(1)
                if 'expiry' in line.lower() or 'valid until' in line.lower():
                    m = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                    if m:
                        from datetime import datetime
                        info['expires_at'] = datetime.strptime(m.group(1), '%Y-%m-%d')
            return info
        except:
            return None
    def get_environment_instance(self, instance_id: str, subaccount_id: str) -> Optional[Dict]:
        try:
            r = self._run(["get", "accounts/environment-instance", instance_id, "-sa", subaccount_id])
            if r.returncode != 0:
                return None
            info = {}
            for line in r.stdout.split('\n'):
                if 'expir' in line.lower() or 'valid until' in line.lower():
                    m = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                    if m:
                        from datetime import datetime
                        info['expires_at'] = datetime.strptime(m.group(1), '%Y-%m-%d')
                if 'state' in line.lower():
                    m = re.search(r'state[:\s]+(\S+)', line, re.I)
                    if m:
                        info['state'] = m.group(1)
            return info
        except:
            return None
    def get_kyma_instance(self, subaccount_id: str) -> Optional[Dict]:
        for i in self.list_environment_instances(subaccount_id):
            if i.get("type") == "kyma":
                return i
        return None
    def get_cf_instance(self, subaccount_id: str) -> Optional[Dict]:
        for i in self.list_environment_instances(subaccount_id):
            if i.get("type") == "cloudfoundry":
                return i
        return None
    def create_kyma_runtime(self, subaccount_id: str, name: str = "kyma") -> Dict:
        r = self._run(["create", "accounts/environment-instance", "--subaccount", subaccount_id,
                      "--environment", "kyma", "--service", "kymaruntime", "--plan", "trial",
                      "--display-name", name, "--parameters", json.dumps({"name": name})], timeout=300)
        return {"success": r.returncode == 0, "output": r.stdout}
def btp_login(subdomain: str, email: str, password: str) -> bool:
    return BTPClient(subdomain, email, password).login()
def verify_account(subdomain: str, email: str, password: str) -> Dict:
    client = BTPClient(subdomain, email, password)
    result = {"valid": False, "subdomain": subdomain, "subaccount_id": None,
              "kyma": None, "cf": None, "error": None}
    if not client.login():
        result["error"] = "Login failed"
        return result
    subaccount_id = client.get_subaccount_id()
    if not subaccount_id:
        result["error"] = "Could not get subaccount ID"
        return result
    result["valid"] = True
    result["subaccount_id"] = subaccount_id
    kyma = client.get_kyma_instance(subaccount_id)
    if kyma:
        result["kyma"] = {"instance_id": kyma["id"], "name": kyma["name"], "state": kyma["state"]}
    cf = client.get_cf_instance(subaccount_id)
    if cf:
        result["cf"] = {"instance_id": cf["id"], "org_name": cf["name"], "state": cf["state"],
                       "api_endpoint": cf.get("api_endpoint")}
    return result
btp_verify_account = verify_account
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        r = verify_account(sys.argv[1], sys.argv[2], sys.argv[3])
        print(json.dumps(r, indent=2))
    else:
        print("Usage: python btp_cli.py <subdomain> <email> <password>")