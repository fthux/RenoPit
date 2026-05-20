"""
File Storage Service — 本地文件存储工具
负责保存上传文件到本地磁盘，提供路径查询
"""

import os
import uuid
from typing import Optional

from ..core.config import settings

# 允许的文件扩展名
ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_FILE_EXT = {'txt', 'md', 'docx', 'pdf'}


def _get_allowed_ext(original_filename: str, file_type: str = 'image') -> str:
    """获取合法扩展名，非法则返回默认扩展名

    Args:
        original_filename: 原始文件名
        file_type: 'image' 或 'file'

    Returns:
        合法的小写扩展名（不含点）或默认扩展名
    """
    allowed = ALLOWED_IMAGE_EXT if file_type == 'image' else ALLOWED_FILE_EXT
    default = 'jpg' if file_type == 'image' else 'txt'

    if '.' not in original_filename:
        return default

    ext = original_filename.rsplit('.', 1)[-1].lower()
    return ext if ext in allowed else default


def generate_storage_filename(original_filename: str, file_type: str = 'image') -> str:
    """为上传文件生成唯一的存储文件名

    Args:
        original_filename: 原始文件名
        file_type: 'image' 或 'file'

    Returns:
        UUID + 合法扩展名，如 'a1b2c3d4.jpg'
    """
    ext = _get_allowed_ext(original_filename, file_type)
    return f"{uuid.uuid4().hex}.{ext}"


def get_storage_dir(project_id: str, file_type: str = 'images') -> str:
    """获取项目文件的存储目录，不存在则自动创建

    Args:
        project_id: 项目 UUID
        file_type: 'images' 或 'files'

    Returns:
        存储目录的绝对路径
    """
    base_dir = settings.UPLOAD_DIR
    sub_dir = 'images' if file_type == 'images' else 'files'
    storage_dir = os.path.join(base_dir, 'projects', project_id, sub_dir)
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir


def get_file_path(project_id: str, file_type: str, filename: str) -> str:
    """返回文件的完整存储路径

    Args:
        project_id: 项目 UUID
        file_type: 'images' 或 'files'
        filename: 文件名（含扩展名）

    Returns:
        文件的绝对路径
    """
    storage_dir = get_storage_dir(project_id, file_type)
    return os.path.join(storage_dir, filename)


async def save_upload_file(
    file,
    project_id: str,
    file_type: str = 'image',
) -> tuple[str, str, int]:
    """保存上传文件到本地磁盘

    Args:
        file: FastAPI UploadFile 对象
        project_id: 项目 UUID
        file_type: 'image' 或 'file'

    Returns:
        (storage_filename, storage_path, file_size) 元组
    """
    original_filename = file.filename or 'unnamed'
    storage_filename = generate_storage_filename(original_filename, file_type)
    storage_dir = get_storage_dir(project_id, 'images' if file_type == 'image' else 'files')
    storage_path = os.path.join(storage_dir, storage_filename)

    # 读取文件内容并写入磁盘
    content = await file.read()
    file_size = len(content)

    with open(storage_path, 'wb') as f:
        f.write(content)

    return storage_filename, storage_path, file_size


def get_report_path(project_id: str) -> str:
    """获取项目 PDF 报告的文件路径

    Args:
        project_id: 项目 UUID

    Returns:
        PDF 报告的完整路径
    """
    report_dir = os.path.join(settings.REPORT_DIR, 'projects', project_id)
    os.makedirs(report_dir, exist_ok=True)
    return os.path.join(report_dir, 'report.pdf')