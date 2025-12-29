from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from .database import Base
from .base import GUID

class CFOrg(Base):
    __tablename__ = "cf_orgs"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    account_id = Column(GUID, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(String(100), unique=True)
    org_name = Column(String(100))
    api_endpoint = Column(String(255))
    status = Column(String(20), nullable=False, default="OK")
    memory_quota_mb = Column(Integer, default=4096)
    memory_used_mb = Column(Integer, default=0)
    active_pattern = Column(String(20), default="7-5")
    active_days_history = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone))
    last_check_at = Column(DateTime)
    failed_count = Column(Integer, default=0)
    
    account = relationship("Account", back_populates="cf_orgs")
