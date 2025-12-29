#!/usr/bin/env python3
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
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('127.0.0.1', port))
                return True
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
    return False
async def _automate_login(url: str, email: str, password: str) -> bool:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return False
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
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
            if "accounts.sap.com" in current_url or "sap.com" in current_url:
                logger.info("On SAP login page, starting automation")
                try:
                    await page.fill('
                    logger.info("Email filled")
                except Exception as e:
                    logger.error(f"Failed to fill email: {e}")
                try:
                    await page.fill('
                    logger.info("Password filled")
                except Exception as e:
                    logger.error(f"Failed to fill password: {e}")
                try:
                    if await page.query_selector('
                        await page.click('
                        logger.info("Continue button clicked")
                        try:
                            await page.wait_for_load_state("networkidle", timeout=15000)
                            logger.info(f"Navigation completed: {page.url[:100]}")
                            page_title = await page.title()
                            if "Terms of Use" in page_title or "terms" in page_title.lower():
                                logger.info("Terms of Use page detected, accepting...")
                                accept_selectors = ['
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
            await asyncio.sleep(3)
            await browser.close()
            logger.info("Login automation completed")
            return True
    except Exception as e:
        logger.error(f"Browser automation failed: {e}")
        return False
def kyma_login(kubeconfig_path: str, email: str, password: str, port: int = 8000) -> bool:
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
    env = _env()
    env['KUBECONFIG'] = kubeconfig_path
    r1 = subprocess.run(['kubectl', 'delete', 'deployment', name, '-n', namespace, '--ignore-not-found'],
                        capture_output=True, text=True, timeout=60, env=env)
    r2 = subprocess.run(['kubectl', 'delete', 'svc', name, '-n', namespace, '--ignore-not-found'],
                        capture_output=True, text=True, timeout=60, env=env)
    return r1.returncode == 0 and r2.returncode == 0
def check_deployment_ready(kubeconfig_path: str, name: str, namespace: str = "default", timeout: int = 120) -> bool:
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