"""
Project 模型 — 项目表
"""

import uuid
import secrets
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def generate_access_token():
    return secrets.token_hex(32)  # 64 位随机访问令牌


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    access_token = Column(String(64), nullable=False, default=generate_access_token)
    status = Column(String(20), nullable=False, default="pending")
    input_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关联
    images = relationship("ProjectImage", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="project", uselist=False, cascade="all, delete-orphan")
    report = relationship("Report", back_populates="project", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_access_token", "access_token"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_created_at", "created_at"),
    )