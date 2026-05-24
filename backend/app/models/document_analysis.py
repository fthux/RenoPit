"""
DocumentAnalysis 模型 — 合同/报价单文档分析结果表
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Text, DateTime, ForeignKey, Uuid, JSON, String, Float, Integer
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(Uuid(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project_file_id = Column(Uuid(as_uuid=False), ForeignKey("project_files.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    doc_type = Column(String(20), default="unknown", nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    summary = Column(Text, nullable=True)
    total_estimated_risk = Column(Text, nullable=True)
    risks_count = Column(Integer, default=0, nullable=False)
    risks_json = Column(JSON, nullable=True)
    classifications_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    project_file = relationship("ProjectFile")