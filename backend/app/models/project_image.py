"""
ProjectImage 模型 — 项目图片关联表（一对多）
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class ProjectImage(Base):
    __tablename__ = "project_images"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(Uuid(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="images")

    __table_args__ = (
        Index("idx_project_images_project_id", "project_id"),
    )