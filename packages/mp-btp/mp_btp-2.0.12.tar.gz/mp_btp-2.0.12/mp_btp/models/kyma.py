from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from .database import Base
from .base import GUID

class KymaRuntime(Base):
    __tablename__ = "kyma_runtimes"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    account_id = Column(GUID, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(String(100), unique=True)
    cluster_name = Column(String(100))
    status = Column(String(20), nullable=False, default="CREATING")
    memory_limit_mb = Column(Integer, default=8192)
    memory_used_mb = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)
    deleted_at = Column(DateTime)
    cooling_until = Column(DateTime)
    failed_count = Column(Integer, default=0)
    last_check_at = Column(DateTime)
    kubeconfig = Column(Text)
    
    account = relationship("Account", back_populates="kyma_runtimes")
