#!/usr/bin/env python3
import subprocess
import re
import json
import os
import logging
from typing import Dict, List, Optional
logger = logging.getLogger(__name__)
class BTPClient:
        try:
            r = self._run(["login", "--url", self.url, "--subdomain", self.subdomain,
                          "--user", self.email, "--password", self.password])
            return r.returncode == 0
        except Exception as e:
            logger.error(f"BTP login failed: {e}")
            return False
    def get_subaccount_id(self) -> Optional[str]:
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
    return BTPClient(subdomain, email, password).login()
def verify_account(subdomain: str, email: str, password: str) -> Dict: