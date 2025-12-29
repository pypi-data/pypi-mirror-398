from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID

# Deployment schemas
class DeploymentCreate(BaseModel):
    image: str
    replicas: int = 1
    memory_mb: int = 4096
    env_type: str = "kyma"
    port: Optional[int] = None
    env_vars: Dict[str, str] = {}
    disk_mb: Optional[int] = None
    expires_in_days: int = 0
    project: str = "default"

class ReplicaResponse(BaseModel):
    replica_index: int
    account_id: UUID
    status: str
    access_url: Optional[str] = None
    started_at: Optional[datetime] = None

class DeploymentResponse(BaseModel):
    deployment_id: UUID
    status: str
    project: str
    image: str
    env_type: str
    replicas: List[ReplicaResponse] = []
    created_at: datetime
    expires_at: Optional[datetime] = None

# Account schemas
class AccountCreate(BaseModel):
    subdomain: str
    email: str
    password: str
    subaccount_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    tags: Dict = {}

class AccountResponse(BaseModel):
    account_id: UUID
    subdomain: str
    email: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"
