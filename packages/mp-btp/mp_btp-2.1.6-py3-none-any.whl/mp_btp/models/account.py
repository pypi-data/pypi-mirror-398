from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from .database import Base
from .base import GUID

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    password = Column(Text, nullable=False)
    
    # 全局账号 (3个月有效)
    subdomain = Column(String(100), nullable=False, unique=True)
    subdomain_expires_at = Column(DateTime)
    
    # 主子账号 (支持 Kyma + CF)
    subaccount_id = Column(String(100))
    region = Column(String(20))  # ap21, us10
    
    # 第二子账号 (只支持 CF，可选)
    subaccount2_id = Column(String(100))
    region2 = Column(String(20))
    
    status = Column(String(20), nullable=False, default="ACTIVE")
    tags = Column(JSON, default={})
    notes = Column(Text)
    preferred_node = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)  # 保留兼容，可用于其他用途
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    kyma_runtimes = relationship("KymaRuntime", back_populates="account", cascade="all, delete-orphan")
    cf_orgs = relationship("CFOrg", back_populates="account", cascade="all, delete-orphan")
