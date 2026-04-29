"""
Dashboard persistence models.
"""
import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class DashboardModel(Base):
    __tablename__ = "dashboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    source_id = Column(String(64), nullable=False)
    question = Column(String(2000), nullable=False)
    sql = Column(String(8000), nullable=True)
    summary = Column(String(8000), nullable=True)
    dashboard_spec = Column(JSON, nullable=False)
    data_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
