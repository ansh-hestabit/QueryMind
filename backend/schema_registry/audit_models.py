"""
QueryMind — Audit Log Models
"""
import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.core.database import Base


class AuditLogModel(Base):
    """Stores query execution history for compliance and governance."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    thread_id = Column(String(255), nullable=True)
    
    question = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    generated_sql = Column(Text, nullable=True)
    
    execution_time_ms = Column(Float, nullable=True)
    row_count = Column(Float, nullable=True)  # Using float to handle large numbers or none safely
    is_success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)

    def __repr__(self):
        status = "Success" if self.is_success else "Failed"
        return f"<AuditLog id={self.id} user={self.user_id} source={self.source_id} status={status}>"
