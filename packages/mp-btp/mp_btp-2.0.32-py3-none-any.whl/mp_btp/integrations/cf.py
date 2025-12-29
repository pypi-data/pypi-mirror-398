#!/usr/bin/env python3
import subprocess
import tempfile
import os
import logging
from typing import Dict, Optional
logger = logging.getLogger(__name__)
def cf_login(api_endpoint: str, email: str, password: str,
             org: Optional[str] = None, space: Optional[str] = None) -> bool:
    cmd = ["cf", "login", "-a", api_endpoint, "-u", email, "-p", password]
    if org:
        cmd.extend(["-o", org])
    if space:
        cmd.extend(["-s", space])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except:
        return False
def cf_target(org: str, space: str = "dev") -> bool:
    try:
        r = subprocess.run(["cf", "target", "-o", org, "-s", space], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            subprocess.run(["cf", "create-space", space], capture_output=True, text=True, timeout=30)
            r = subprocess.run(["cf", "target", "-o", org, "-s", space], capture_output=True, text=True, timeout=30)
        subprocess.run(["cf", "allow-space-ssh", space], capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except:
        return False
def cf_get_quota(org: str) -> Dict:
    try:
        r = subprocess.run(["cf", "org", org], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return {"valid": False, "error": "Cannot get org info"}
        quota_name = None
        for line in r.stdout.split('\n'):
            if 'quota:' in line.lower():
                quota_name = line.split(':')[-1].strip()
                break
        if not quota_name:
            return {"valid": False, "error": "Cannot find quota name"}
        r = subprocess.run(["cf", "quota", quota_name], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return {"valid": False, "error": "Cannot get quota details"}
        quota = {"valid": True, "quota_name": quota_name, "memory_mb": 0, "routes": 0, "app_instances": 0}
        for line in r.stdout.split('\n'):
            ll = line.lower()
            val = line.split(':')[-1].strip() if ':' in line else ""
            if 'total memory:' in ll:
                if val.endswith('G'):
                    quota["memory_mb"] = int(float(val[:-1]) * 1024)
                elif val.endswith('M'):
                    quota["memory_mb"] = int(val[:-1])
                elif val.isdigit():
                    quota["memory_mb"] = int(val)
            elif 'routes:' in ll and val.isdigit():
                quota["routes"] = int(val)
            elif 'app instances:' in ll and val.isdigit():
                quota["app_instances"] = int(val)
        return quota
    except Exception as e:
        return {"valid": False, "error": str(e)}
def cf_push(name: str, image: str, memory_mb: int = 256, disk_mb: int = 512,
            env_vars: Optional[Dict] = None, enable_ssh: bool = True) -> Dict:
    try:
        import yaml
    except ImportError:
        return {"success": False, "error": "PyYAML not installed"}
    manifest = {"applications": [{"name": name, "docker": {"image": image},
                                  "memory": f"{memory_mb}M", "disk_quota": f"{disk_mb}M", "instances": 1}]}
    if env_vars:
        manifest["applications"][0]["env"] = env_vars
    fd, path = tempfile.mkstemp(suffix='.yml')
    try:
        with os.fdopen(fd, 'w') as f:
            yaml.dump(manifest, f)
        r = subprocess.run(["cf", "push", "-f", path], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return {"success": False, "error": r.stderr or r.stdout}
        if enable_ssh:
            subprocess.run(["cf", "enable-ssh", name], capture_output=True, text=True, timeout=30)
        url = None
        for line in r.stdout.split('\n'):
            if 'routes:' in line.lower():
                route = line.split(':')[-1].strip()
                if route:
                    url = f"https://{route}"
                break
        return {"success": True, "url": url}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if os.path.exists(path):
            os.unlink(path)
def cf_stop(name: str) -> bool:
    try:
        r = subprocess.run(["cf", "stop", name], capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except:
        return False
def cf_start(name: str) -> bool:
    try:
        r = subprocess.run(["cf", "start", name], capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except:
        return False
def cf_restart(name: str) -> bool:
    try:
        r = subprocess.run(["cf", "restart", name], capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except:
        return False
def cf_delete(name: str, delete_routes: bool = True) -> bool:
    try:
        cmd = ["cf", "delete", name, "-f"]
        if delete_routes:
            cmd.append("-r")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except:
        return False
def cf_apps() -> list:
    try:
        r = subprocess.run(["cf", "apps"], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return []
        apps, in_data = [], False
        for line in r.stdout.split('\n'):
            if line.startswith('name'):
                in_data = True
                continue
            if in_data and line.strip():
                parts = line.split()
                if parts:
                    apps.append({"name": parts[0], "state": parts[1] if len(parts) > 1 else "unknown"})
        return apps
    except:
        return []
cf_target_space = cf_target
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        if cf_login(sys.argv[1], sys.argv[2], sys.argv[3]):
            print("Login OK")
            if len(sys.argv) >= 5:
                print(cf_get_quota(sys.argv[4]))
        else:
            print("Login failed")
    else:
        print("Usage: python cf.py <api_endpoint> <email> <password> [org]")