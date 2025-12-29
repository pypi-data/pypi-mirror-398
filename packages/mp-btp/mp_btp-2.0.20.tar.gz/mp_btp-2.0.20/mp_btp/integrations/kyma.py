#!/usr/bin/env python3
"""
Kyma - SAP Kyma deployment utilities with OIDC login automation.
Single-file module, copy and use directly.

Requirements: pyyaml, playwright (for OIDC login)

Usage:
    from kyma import kyma_login, kyma_deploy, kyma_delete, download_kubeconfig
    
    download_kubeconfig("instance-id", "/tmp/kubeconfig.yaml")
    kyma_login("/tmp/kubeconfig.yaml", "email@example.com", "password")
    result = kyma_deploy("/tmp/kubeconfig.yaml", "my-app", "nginx:alpine", port=80)
    kyma_delete("/tmp/kubeconfig.yaml", "my-app")
"""
import asyncio
import subprocess
import time
import os
import socket
import logging
import yaml
from typing import Dict, Optional

logger = logging.getLogger(__name__)
TOOL_PATH = os.environ.get("BTP_TOOL_PATH", "/tmp/tool_cache/bin")


def _env() -> dict:
    env = os.environ.copy()
    if TOOL_PATH not in env.get('PATH', ''):
        env['PATH'] = f"{TOOL_PATH}:{env.get('PATH', '')}"
    return env


def download_kubeconfig(instance_id: str, output_path: str) -> bool:
    """Download kubeconfig from Kyma broker."""
    url = f"https://kyma-env-broker.cp.kyma.cloud.sap/kubeconfig/{instance_id}"
    try:
        r = subprocess.run(['curl', '-s', url, '-o', output_path], capture_output=True, timeout=30)
        if r.returncode == 0 and os.path.exists(output_path):
            with open(output_path) as f:
                yaml.safe_load(f)
            return True
        return False
    except:
        return False


def _extract_oidc(kubeconfig_path: str) -> Optional[Dict]:
    try:
        with open(kubeconfig_path) as f:
            cfg = yaml.safe_load(f)
        ctx = cfg.get('current-context')
        for u in cfg.get('users', []):
            if u.get('name') == ctx:
                args = u.get('user', {}).get('exec', {}).get('args', [])
                oidc = {}
                for a in args:
                    if a.startswith('--oidc-issuer-url='):
                        oidc['issuer_url'] = a.split('=', 1)[1]
                    elif a.startswith('--oidc-client-id='):
                        oidc['client_id'] = a.split('=', 1)[1]
                return oidc if oidc else None
        return None
    except:
        return None


def _wait_port(port: int, timeout: int = 10) -> bool:
    """Wait for a port to be listening (something is serving on it)."""
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('127.0.0.1', port))
                return True  # Port is listening
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
    return False


async def _automate_login(url: str, email: str, password: str) -> bool:
    """
    Automate OIDC login via kubelogin's local server.
    Based on ref/kyma-login.py
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return False
    
    try:
        async with async_playwright() as p:
            # Use incognito mode to avoid session conflicts
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()  # New context = clean session
            page = await context.new_page()
            
            # Navigate to kubelogin's local server
            logger.info(f"Navigating to: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                logger.error(f"Failed to connect to {url}: {e}")
                await browser.close()
                return False
            
            await asyncio.sleep(1)
            current_url = page.url
            logger.info(f"Page loaded: {current_url[:100]}")
            
            # Check if we're on the SAP login page
            if "accounts.sap.com" in current_url or "sap.com" in current_url:
                logger.info("On SAP login page, starting automation")
                
                # Fill email using j_username field
                try:
                    await page.fill('#j_username', email)
                    logger.info("Email filled")
                except Exception as e:
                    logger.error(f"Failed to fill email: {e}")
                
                # Fill password using j_password field
                try:
                    await page.fill('#j_password', password)
                    logger.info("Password filled")
                except Exception as e:
                    logger.error(f"Failed to fill password: {e}")
                
                # Click Continue button
                try:
                    if await page.query_selector('#logOnFormSubmit'):
                        await page.click('#logOnFormSubmit')
                        logger.info("Continue button clicked")
                        
                        # Wait for navigation after login
                        try:
                            await page.wait_for_load_state("networkidle", timeout=15000)
                            logger.info(f"Navigation completed: {page.url[:100]}")
                            
                            # Check if Terms of Use page appeared
                            page_title = await page.title()
                            if "Terms of Use" in page_title or "terms" in page_title.lower():
                                logger.info("Terms of Use page detected, accepting...")
                                # Look for accept button
                                accept_selectors = ['#acceptButton', 'button[type="submit"]', '.accept-button', 'input[value="Accept"]']
                                for selector in accept_selectors:
                                    if await page.query_selector(selector):
                                        await page.click(selector)
                                        logger.info("Terms accepted")
                                        await page.wait_for_load_state("networkidle", timeout=10000)
                                        break
                        except asyncio.TimeoutError:
                            logger.warning("Navigation timeout (may be normal)")
                    else:
                        logger.warning("Continue button not found")
                except Exception as e:
                    logger.error(f"Error during login: {e}")
                    
            elif "localhost" in current_url or "127.0.0.1" in current_url:
                logger.info("Already on kubelogin callback page")
            else:
                logger.warning(f"Unexpected page: {current_url}")
            
            # Wait for token processing
            await asyncio.sleep(3)
            await browser.close()
            logger.info("Login automation completed")
            return True
            
    except Exception as e:
        logger.error(f"Browser automation failed: {e}")
        return False


def kyma_login(kubeconfig_path: str, email: str, password: str, port: int = 8000) -> bool:
    """Login to Kyma cluster using OIDC automation."""
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    
    # Check if already logged in with valid token for the same cluster
    try:
        # Get current cluster from kubeconfig
        with open(kubeconfig_path) as f:
            import yaml
            config = yaml.safe_load(f)
            current_cluster = None
            if config.get('clusters'):
                current_cluster = config['clusters'][0].get('cluster', {}).get('server')
        
        # Try kubectl to check if token is valid
        r = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, timeout=5, env=env)
        if r.returncode == 0 and current_cluster and current_cluster in r.stdout:
            logger.info(f"Already logged in to {current_cluster[:50]}...")
            return True
    except (subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"Token check failed: {e}")
    
    # If not logged in or different cluster, clear ALL kubectl cache
    try:
        import shutil
        from pathlib import Path
        cache_dir = Path.home() / '.kube' / 'cache'
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            logger.info("Cleared kubectl cache (including oidc-login)")
    except Exception as e:
        logger.warning(f"Could not clear cache: {e}")
    
    logger.info("Starting fresh login")
    
    oidc = _extract_oidc(kubeconfig_path)
    if not oidc:
        logger.error("Failed to extract OIDC config")
        return False
    
    logger.info(f"Starting kubelogin on port {port}")
    cmd = [
        "kubelogin", "get-token", f"--oidc-issuer-url={oidc['issuer_url']}",
        f"--oidc-client-id={oidc['client_id']}", "--oidc-extra-scope=email",
        "--oidc-extra-scope=openid", "--skip-open-browser", f"--listen-address=127.0.0.1:{port}"
    ]
    logger.debug(f"Command: {' '.join(cmd)}")
    logger.debug(f"PATH: {env.get('PATH', '')[:100]}")
    
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    except FileNotFoundError:
        logger.error("kubelogin not found")
        return False
    
    try:
        if not _wait_port(port, timeout=10):
            logger.error(f"Port {port} not available")
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                logger.error(f"kubelogin stderr: {stderr[:200]}")
                if '"token"' in stdout:
                    try:
                        r = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, timeout=5, env=env)
                        return r.returncode == 0
                    except subprocess.TimeoutExpired:
                        return False
            proc.terminate()
            return False
        
        logger.info(f"Port {port} ready, starting browser automation")
        time.sleep(1)
        if not asyncio.run(_automate_login(f"http://127.0.0.1:{port}", email, password)):
            logger.error("Browser automation failed")
            return False
        
        logger.info("Browser automation completed, checking kubectl")
        time.sleep(2)
        try:
            r = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, timeout=10, env=env)
            success = r.returncode == 0
            if success:
                logger.info("Login successful")
            else:
                logger.error(f"kubectl failed: {r.stderr[:200]}")
            return success
        except subprocess.TimeoutExpired:
            logger.error("kubectl timeout")
            return False
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()


def kyma_deploy(kubeconfig_path: str, name: str, image: str, port: Optional[int] = None,
                memory_mb: int = 256, env_vars: Optional[Dict] = None, namespace: str = "default") -> Dict:
    """Deploy to Kyma cluster."""
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    
    dep = {
        'apiVersion': 'apps/v1', 'kind': 'Deployment',
        'metadata': {'name': name, 'namespace': namespace},
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
            'metadata': {'name': name, 'namespace': namespace},
            'spec': {'selector': {'app': name}, 'ports': [{'port': port, 'targetPort': port}], 'type': 'ClusterIP'}
        })
    
    manifest_yaml = '---\n'.join(yaml.dump(m) for m in manifests)
    r = subprocess.run(['kubectl', 'apply', '-f', '-'], input=manifest_yaml, capture_output=True, text=True, timeout=60, env=env)
    
    if r.returncode != 0:
        return {'success': False, 'error': r.stderr}
    
    url = None
    if port:
        r2 = subprocess.run(['kubectl', 'get', 'svc', name, '-n', namespace, '-o', 'jsonpath={.spec.clusterIP}:{.spec.ports[0].port}'],
                           capture_output=True, text=True, timeout=30, env=env)
        if r2.returncode == 0 and r2.stdout:
            url = f"http://{r2.stdout}"
    
    return {'success': True, 'url': url}


def kyma_deploy_raw_yaml(kubeconfig_path: str, yaml_content: str, namespace: str = "demo") -> Dict:
    """Deploy raw K8s YAML to Kyma cluster."""
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    
    # Create namespace if not exists
    subprocess.run(['kubectl', 'create', 'namespace', namespace, '--dry-run=client', '-o', 'yaml'], 
                  capture_output=True, env=env)
    subprocess.run(['kubectl', 'apply', '-f', '-'], 
                  input=f"apiVersion: v1\nkind: Namespace\nmetadata:\n  name: {namespace}\n",
                  capture_output=True, text=True, env=env)
    
    # Apply YAML to the namespace
    r = subprocess.run(['kubectl', 'apply', '-f', '-', '-n', namespace], 
                      input=yaml_content, capture_output=True, text=True, timeout=120, env=env)
    
    if r.returncode != 0:
        return {'success': False, 'error': r.stderr}
    
    return {'success': True, 'output': r.stdout}


def kyma_delete(kubeconfig_path: str, name: str, namespace: str = "default") -> bool:
    """Delete Kyma deployment and service."""
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    r1 = subprocess.run(['kubectl', 'delete', 'deployment', name, '-n', namespace, '--ignore-not-found'],
                        capture_output=True, text=True, timeout=60, env=env)
    r2 = subprocess.run(['kubectl', 'delete', 'svc', name, '-n', namespace, '--ignore-not-found'],
                        capture_output=True, text=True, timeout=60, env=env)
    return r1.returncode == 0 and r2.returncode == 0


def check_deployment_ready(kubeconfig_path: str, name: str, namespace: str = "default", timeout: int = 120) -> bool:
    """Wait for deployment to be ready."""
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    try:
        r = subprocess.run(['kubectl', 'rollout', 'status', f'deployment/{name}', '-n', namespace, f'--timeout={timeout}s'],
                          capture_output=True, text=True, timeout=timeout + 10, env=env)
        return r.returncode == 0
    except:
        return False


def get_service_url(kubeconfig_path: str, name: str, namespace: str = "default") -> Optional[str]:
    """Get service URL."""
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    try:
        r = subprocess.run(['kubectl', 'get', 'svc', name, '-n', namespace, '-o', 'jsonpath={.spec.clusterIP}:{.spec.ports[0].port}'],
                          capture_output=True, text=True, timeout=30, env=env)
        return f"http://{r.stdout}" if r.returncode == 0 and r.stdout else None
    except:
        return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        print(f"Login: {kyma_login(sys.argv[1], sys.argv[2], sys.argv[3])}")
    else:
        print("Usage: python kyma.py <kubeconfig> <email> <password>")
