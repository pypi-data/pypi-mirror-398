#!/usr/bin/env python3
"""
Proxy pool support for single-node deployment.
Rotates proxies for BTP/CF/Kyma operations to improve anonymity.

Usage:
    from mp_btp.integrations.proxy_pool import ProxyPool, with_proxy
    
    pool = ProxyPool.from_config()
    
    # Get proxy for account
    proxy = pool.get_proxy_for_account(account)
    
    # Use with subprocess
    env = with_proxy(proxy)
    subprocess.run(["btp", "login", ...], env=env)
"""
import os
import random
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Proxy configuration."""
    url: str  # http://user:pass@host:port or socks5://host:port
    protocol: str  # http, https, socks5
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    tags: List[str] = None  # region tags: us, eu, asia
    
    @classmethod
    def from_url(cls, url: str, tags: List[str] = None):
        """Parse proxy URL."""
        parsed = urlparse(url)
        return cls(
            url=url,
            protocol=parsed.scheme,
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            tags=tags or []
        )
    
    def to_env(self) -> Dict[str, str]:
        """Convert to environment variables."""
        env = {}
        if self.protocol in ["http", "https"]:
            env["HTTP_PROXY"] = self.url
            env["HTTPS_PROXY"] = self.url
        elif self.protocol == "socks5":
            env["ALL_PROXY"] = self.url
        env["NO_PROXY"] = "localhost,127.0.0.1"
        return env


class ProxyPool:
    """Proxy pool with account affinity."""
    
    def __init__(self, proxies: List[Proxy]):
        self.proxies = proxies
        self.account_proxy_map: Dict[str, Proxy] = {}  # account_id -> proxy
    
    @classmethod
    def from_config(cls, config: Dict = None):
        """Load from config."""
        if not config:
            from mp_btp.config import get_config
            config = get_config().get("proxy_pool", {})
        
        if not config.get("enabled"):
            return None
        
        proxies = []
        for p in config.get("proxies", []):
            proxy = Proxy.from_url(p["url"], p.get("tags"))
            proxies.append(proxy)
        
        if not proxies:
            logger.warning("Proxy pool enabled but no proxies configured")
            return None
        
        logger.info(f"Loaded {len(proxies)} proxies")
        return cls(proxies)
    
    @classmethod
    def from_env(cls):
        """Load from environment variable PROXY_LIST."""
        proxy_list = os.environ.get("PROXY_LIST", "")
        if not proxy_list:
            return None
        
        proxies = []
        for url in proxy_list.split(","):
            url = url.strip()
            if url:
                proxies.append(Proxy.from_url(url))
        
        return cls(proxies) if proxies else None
    
    def get_proxy_for_account(self, account, region_hint: str = None) -> Optional[Proxy]:
        """
        Get proxy for account with affinity.
        
        Priority:
        1. Previously used proxy (affinity)
        2. Region-matched proxy
        3. Random proxy
        """
        account_id = str(account.id)
        
        # 1. Check affinity
        if account_id in self.account_proxy_map:
            proxy = self.account_proxy_map[account_id]
            logger.debug(f"Using affinity proxy {proxy.host} for {account.subdomain}")
            return proxy
        
        # 2. Filter by region
        candidates = self.proxies
        if region_hint:
            region_proxies = [p for p in self.proxies if region_hint in p.tags]
            if region_proxies:
                candidates = region_proxies
        
        # 3. Random selection
        proxy = random.choice(candidates)
        self.account_proxy_map[account_id] = proxy
        
        logger.info(f"Assigned proxy {proxy.host} to {account.subdomain}")
        return proxy
    
    def get_random_proxy(self, region: str = None) -> Optional[Proxy]:
        """Get random proxy, optionally filtered by region."""
        candidates = self.proxies
        if region:
            region_proxies = [p for p in self.proxies if region in p.tags]
            if region_proxies:
                candidates = region_proxies
        return random.choice(candidates) if candidates else None


def with_proxy(proxy: Optional[Proxy], base_env: Dict = None) -> Dict[str, str]:
    """
    Create environment dict with proxy settings.
    
    Usage:
        env = with_proxy(proxy)
        subprocess.run(["btp", "login", ...], env=env)
    """
    env = dict(os.environ)
    if base_env:
        env.update(base_env)
    
    if proxy:
        env.update(proxy.to_env())
    
    return env


# Global pool instance
_pool: Optional[ProxyPool] = None


def get_proxy_pool() -> Optional[ProxyPool]:
    """Get global proxy pool instance."""
    global _pool
    if _pool is None:
        _pool = ProxyPool.from_config() or ProxyPool.from_env()
    return _pool
