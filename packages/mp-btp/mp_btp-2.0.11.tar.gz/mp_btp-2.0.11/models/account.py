from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from .database import Base
from .base import GUID

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    subdomain = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False)
    password = Column(Text, nullable=False)
    subaccount_id = Column(String(100))
    status = Column(String(20), nullable=False, default="ACTIVE")
    tags = Column(JSON, default={})
    notes = Column(Text)
    preferred_node = Column(String(100))  # Node affinity for multi-node execution
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    kyma_runtimes = relationship("KymaRuntime", back_populates="account", cascade="all, delete-orphan")
    cf_orgs = relationship("CFOrg", back_populates="account", cascade="all, delete-orphan")
