"""
Analysis 模型 — 分析结果表
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Text, DateTime, ForeignKey, Uuid, JSON, String
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(Uuid(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    raw_result_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="analysis")
    report = relationship("Report", back_populates="analysis", uselist=False, cascade="all, delete-orphan")

    # 注：project_id 不设 UNIQUE 约束，与 04-database-schema.md 一致
