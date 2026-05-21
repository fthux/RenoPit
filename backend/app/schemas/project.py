"""
Project Schemas — 项目相关的 Pydantic 请求/响应模型
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """创建项目请求体"""
    name: str = Field(..., max_length=255, description="项目名称")
    description: Optional[str] = Field(default=None, max_length=500, description="项目描述")


class ProjectStatusResponse(BaseModel):
    """项目状态响应"""
    id: str
    status: str  # pending / analyzing / completed / failed
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    """项目详情响应"""
    id: str
    name: str
    description: Optional[str] = None
    access_token: str = ""
    status: str
    input_text: Optional[str] = None
    image_count: int = 0
    file_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    projects: List[ProjectResponse]
    total: int