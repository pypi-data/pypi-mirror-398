from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from datetime import datetime, UTC
import uuid
from .database import Base
from .base import GUID

class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    operation_type = Column(String(50), nullable=False)
    account_id = Column(GUID, ForeignKey("accounts.id"))
    deployment_id = Column(GUID, ForeignKey("deployments.id"))
    replica_id = Column(GUID, ForeignKey("deployment_replicas.id"))
    status = Column(String(20), nullable=False)
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
