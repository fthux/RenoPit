"""
File Schemas — 文件上传相关的 Pydantic 响应模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """文件上传成功后的响应"""
    id: str
    original_filename: str
    file_type: str  # image / txt / md / docx / pdf
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileResponse(BaseModel):
    """文件信息响应"""
    id: str
    project_id: str
    original_filename: str
    storage_path: str
    file_type: str
    extracted_text: Optional[str] = None
    file_size: int
    width: Optional[int] = None  # 仅图片类型
    height: Optional[int] = None  # 仅图片类型
    created_at: datetime

    model_config = {"from_attributes": True}