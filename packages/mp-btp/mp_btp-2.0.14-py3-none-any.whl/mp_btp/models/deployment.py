from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from .database import Base
from .base import GUID

class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project = Column(String(100), default="default")
    env_type = Column(String(10), nullable=False)
    image = Column(String(255), nullable=False)
    replicas = Column(Integer, default=1)
    memory_mb = Column(Integer, nullable=False)
    disk_mb = Column(Integer)
    port = Column(Integer)
    env_vars = Column(JSON, default={})
    raw_yaml = Column(Text)  # 原始 K8s YAML 或 compose
    deploy_type = Column(String(20), default='manual')  # manual | compose | k8s-yaml
    status = Column(String(20), nullable=False, default="PENDING")
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone), onupdate=lambda: datetime.now(timezone))
    
    replicas_list = relationship("DeploymentReplica", back_populates="deployment", cascade="all, delete-orphan")


class DeploymentReplica(Base):
    __tablename__ = "deployment_replicas"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    deployment_id = Column(GUID, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    replica_index = Column(Integer, nullable=False)
    account_id = Column(GUID, ForeignKey("accounts.id"), nullable=False)
    runtime_id = Column(GUID)
    runtime_type = Column(String(10), nullable=False)
    container_name = Column(String(255))
    access_url = Column(String(500))
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone))
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    
    deployment = relationship("Deployment", back_populates="replicas_list")
