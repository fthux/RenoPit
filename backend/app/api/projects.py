"""
项目相关 API 端点
"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..schemas import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectListResponse,
    AnalysisResponse,
)


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    tokens: Optional[str] = Query(None, description="逗号分隔的 access_token 列表"),
    db: Session = Depends(get_db),
):
    """
    根据 access_token 查询项目列表（历史记录）
    前端传入 localStorage 中保存的 tokens
    """
    return ProjectListResponse(projects=[], total=0)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    input_text: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    """
    创建分析项目
    - 接收多图 + 文本文件 + 文本描述
    - 至少一项非空校验
    - 返回项目信息（含 access_token）
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """查询项目详情"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(
    project_id: str,
    db: Session = Depends(get_db),
):
    """获取分析结果 JSON"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}/report")
async def download_report(
    project_id: str,
    db: Session = Depends(get_db),
):
    """下载 PDF 报告（按需生成）"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}/events")
async def stream_events(
    project_id: str,
    db: Session = Depends(get_db),
):
    """SSE 实时状态推送"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}/images/{image_id}")
async def get_image(
    project_id: str,
    image_id: str,
    db: Session = Depends(get_db),
):
    """获取上传的图片"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{project_id}/files/{file_id}")
async def get_file(
    project_id: str,
    file_id: str,
    db: Session = Depends(get_db),
):
    """获取上传的文本文件"""
    raise HTTPException(status_code=501, detail="Not implemented yet")