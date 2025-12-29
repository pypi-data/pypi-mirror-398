from sqlalchemy import String, TypeDecorator
from sqlalchemy.types import CHAR
import uuid

class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses String(36) for SQLite."""
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(uuid.UUID(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)
        return value
    
    def copy(self, **kw):
        return GUID()
