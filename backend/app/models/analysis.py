"""
Analysis 模型 — 分析结果表
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    raw_result_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="analysis")
    report = relationship("Report", back_populates="analysis", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", name="uq_analyses_project_id"),
    )