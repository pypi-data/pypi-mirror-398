import os
import yaml
from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus
from typing import Optional

def _decode_config(encoded: str) -> str:
    """解码配置（Base64 + 反转）"""
    import base64
    return base64.b64decode(encoded[::-1]).decode()

class Settings(BaseSettings):
    database_url: Optional[str] = None
    supabase_url: str = ""
    supabase_key: str = ""
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
    
    def model_post_init(self, __context):
        # 默认使用 Supabase PostgreSQL（加密存储）
        if not self.database_url:
            # 加密的 URI
            encrypted_uri = "zVmcnR3cvB3LzQTN2oTbvNmLlNXYiFGc1NnLyVGbv9GcuETL0NXYlhGd192ctAXYtETLzdXYARFM0UCMzIDMlR2YiFmOop3crJ3dipHb2pGalh3ZsRmbjFnLzVmcnR3cvB3LvoDbxNXZydGdz9Gc"
            self.database_url = _decode_config(encrypted_uri)

@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)
