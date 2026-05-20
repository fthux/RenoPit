"""
Report 模型 — PDF 报告表
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(UUID(as_uuid=False), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="report")
    analysis = relationship("Analysis", back_populates="report")

    __table_args__ = (
        UniqueConstraint("analysis_id", name="uq_reports_analysis_id"),
    )