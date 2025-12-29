#!/usr/bin/env python3
import subprocess
import tempfile
import os
import logging
from typing import Dict, Optional
logger = logging.getLogger(__name__)
def cf_login(api_endpoint: str, email: str, password: str,
             org: Optional[str] = None, space: Optional[str] = None) -> bool:
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
        r = subprocess.run(["cf", "start", name], capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except:
        return False
def cf_restart(name: str) -> bool:
    try:
        cmd = ["cf", "delete", name, "-f"]
        if delete_routes:
            cmd.append("-r")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except:
        return False
def cf_apps() -> list: