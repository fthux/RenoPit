"""
ProjectFile 模型 — 项目文本文件关联表（一对多）
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(Uuid(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # txt / md / docx / pdf
    extracted_text = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="files")

    __table_args__ = (
        Index("idx_project_files_project_id", "project_id"),
    )