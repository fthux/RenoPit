"""
Project API — matches frontend routes at /api/projects/*
"""

import asyncio
import logging
import os
import secrets
import uuid
from typing import Optional, List

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Project, ProjectImage, ProjectFile, Analysis, Report
from ..schemas import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectListResponse,
    AnalysisResponse,
)
from ..services.file_storage import save_upload_file
from ..services.file_parser import extract_text
from ..services.image_processor import compress_image, get_image_dimensions
from ..services.sse_manager import sse_manager
from ..services.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _generate_access_token() -> str:
    return secrets.token_hex(32)


# ── GET /api/projects — list all projects ──────────────────────────
@router.get("/", response_model=ProjectListResponse)
async def list_projects(db: Session = Depends(get_db)):
    projects_orm = (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .all()
    )
    project_list = [_project_to_response(p) for p in projects_orm]
    return ProjectListResponse(projects=project_list, total=len(project_list))


# ── POST /api/projects — create project (JSON body) ────────────────
@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreateRequest = Body(...),
    input_text: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    """
    Create a new project with optional files.
    Accepts both JSON body (name/description) and multipart files.
    """
    project = Project(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        access_token=_generate_access_token(),
        status="pending",
        input_text=input_text,
    )
    db.add(project)
    db.flush()

    # Save images
    if images:
        for img_file in images:
            if not img_file.filename:
                continue
            storage_filename, storage_path, file_size = await save_upload_file(
                img_file, project.id, file_type="image"
            )
            compress_image(storage_path)
            width, height = get_image_dimensions(storage_path)
            db.add(ProjectImage(
                id=str(uuid.uuid4()),
                project_id=project.id,
                original_filename=img_file.filename,
                storage_path=storage_path,
                file_size=file_size,
                width=width,
                height=height,
            ))

    # Save text files
    if files:
        for txt_file in files:
            if not txt_file.filename:
                continue
            original_name = txt_file.filename or "unnamed"
            file_type = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "txt"
            storage_filename, storage_path, file_size = await save_upload_file(
                txt_file, project.id, file_type="file"
            )
            try:
                extracted = extract_text(storage_path, file_type)
            except ValueError:
                extracted = ""
            db.add(ProjectFile(
                id=str(uuid.uuid4()),
                project_id=project.id,
                original_filename=original_name,
                storage_path=storage_path,
                file_type=file_type,
                extracted_text=extracted,
                file_size=file_size,
            ))

    db.commit()
    db.refresh(project)

    # Enqueue async analysis
    try:
        from ..tasks.analysis import run_analysis_task
        run_analysis_task.delay(str(project.id))
    except Exception as e:
        logger.error(f"Failed to enqueue Celery task: {e}")

    return _project_to_response(project)


# ── DELETE /api/projects/:id — delete project ──────────────────────
@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"detail": "ok"}


# ── GET /api/projects/:id — project detail ─────────────────────────
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _project_to_response(project)


# ── POST /api/projects/:id/upload — upload files ───────────────────
@router.post("/{project_id}/upload")
async def upload_files(
    project_id: str,
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个文件")

    saved_files = []
    saved_images = []

    for f in files:
        if not f.filename:
            continue
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        is_image = ext in ("png", "jpg", "jpeg", "webp", "gif", "bmp")

        if is_image:
            storage_filename, storage_path, file_size = await save_upload_file(
                f, project_id, file_type="image"
            )
            compress_image(storage_path)
            width, height = get_image_dimensions(storage_path)
            img = ProjectImage(
                id=str(uuid.uuid4()),
                project_id=project_id,
                original_filename=f.filename,
                storage_path=storage_path,
                file_size=file_size,
                width=width,
                height=height,
            )
            db.add(img)
            saved_images.append(img)
        else:
            storage_filename, storage_path, file_size = await save_upload_file(
                f, project_id, file_type="file"
            )
            try:
                extracted = extract_text(storage_path, ext)
            except ValueError:
                extracted = ""
            pf = ProjectFile(
                id=str(uuid.uuid4()),
                project_id=project_id,
                original_filename=f.filename,
                storage_path=storage_path,
                file_type=ext,
                extracted_text=extracted,
                file_size=file_size,
            )
            db.add(pf)
            saved_files.append(pf)

    db.commit()
    return {
        "detail": "ok",
        "files": len(saved_files),
        "images": len(saved_images),
    }


# ── GET /api/projects/:id/files — list project files ───────────────
@router.get("/{project_id}/files")
async def list_files(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
    return [
        {
            "id": f.id,
            "project_id": f.project_id,
            "original_name": f.original_filename,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "parsed_content": f.extracted_text if f.extracted_text else None,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


# ── GET /api/projects/:id/images — list project images ─────────────
@router.get("/{project_id}/images")
async def list_images(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    images = db.query(ProjectImage).filter(ProjectImage.project_id == project_id).all()
    return [
        {
            "id": img.id,
            "project_id": img.project_id,
            "original_name": img.original_filename,
            "file_size": img.file_size,
            "width": img.width,
            "height": img.height,
            "created_at": img.created_at.isoformat() if img.created_at else None,
        }
        for img in images
    ]


# ── GET /api/projects/:id/analysis — get analysis JSON ─────────────
@router.get("/{project_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id, Analysis.status == "completed")
        .order_by(Analysis.completed_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果尚未生成")

    return AnalysisResponse(
        id=analysis.id,
        project_id=analysis.project_id,
        status=analysis.status,
        problems_count=len(analysis.raw_result_json.get("problems", [])) if analysis.raw_result_json else 0,
        result_json=analysis.raw_result_json,
        error_message=analysis.error_message,
        completed_at=analysis.completed_at,
        created_at=analysis.created_at,
    )


# ── GET /api/projects/:id/analyze/stream — SSE analysis stream ─────
@router.get("/{project_id}/analyze/stream")
async def stream_analysis(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    queue = sse_manager.subscribe(project_id)

    async def event_generator():
        try:
            yield f"event: status_change\ndata: {{\"project_id\":\"{project_id}\",\"status\":\"{project.status}\",\"message\":\"已连接\"}}\n\n"
            while True:
                try:
                    sse_message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield sse_message
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.unsubscribe(project_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /api/projects/:id/report — report info (JSON) ──────────────
@router.get("/{project_id}/report")
async def get_report_info(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id, Analysis.status == "completed")
        .order_by(Analysis.completed_at.desc())
        .first()
    )

    report_record = db.query(Report).filter(Report.project_id == project_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="请先完成分析")

    result = analysis.raw_result_json or {}
    summary_from_json = result.get("summary", {})
    summary = {
        "total_pitfalls": summary_from_json.get("total_pitfalls", 0),
        "critical_count": summary_from_json.get("critical_count", 0),
        "high_count": summary_from_json.get("high_count", 0),
        "medium_count": summary_from_json.get("medium_count", 0),
        "low_count": summary_from_json.get("low_count", 0),
        "score": summary_from_json.get("score", 0),
    }

    return {
        "id": report_record.id if report_record else project_id,
        "project_id": project_id,
        "pdf_path": report_record.pdf_storage_path if report_record else None,
        "summary": summary,
        "pitfalls_count": len(result.get("problems", [])),
        "generated_at": report_record.created_at.isoformat() if report_record and report_record.created_at else None,
    }


# ── GET /api/projects/:id/report/pdf — download PDF ────────────────
@router.get("/{project_id}/report/pdf")
async def download_report_pdf(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    pdf_bytes = generate_pdf(project_id)
    if pdf_bytes is None:
        raise HTTPException(status_code=503, detail="PDF 生成失败，请确认分析已完成")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=renovation-report-{project_id[:8]}.pdf",
        },
    )


# ── GET /api/projects/:id/images/:image_id — serve image file ─────
@router.get("/{project_id}/images/{image_id}")
async def get_image_file(project_id: str, image_id: str, db: Session = Depends(get_db)):
    image = (
        db.query(ProjectImage)
        .filter(ProjectImage.id == image_id, ProjectImage.project_id == project_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    if not os.path.exists(image.storage_path):
        raise HTTPException(status_code=404, detail="图片文件已丢失")

    ext = image.storage_path.rsplit(".", 1)[-1].lower() if "." in image.storage_path else "jpg"
    media_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
    return FileResponse(path=image.storage_path, media_type=media_types.get(ext, "image/jpeg"))


# ── GET /api/projects/:id/files/:file_id — serve file download ────
@router.get("/{project_id}/files/{file_id}")
async def get_file_download(project_id: str, file_id: str, db: Session = Depends(get_db)):
    file_record = (
        db.query(ProjectFile)
        .filter(ProjectFile.id == file_id, ProjectFile.project_id == project_id)
        .first()
    )
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not os.path.exists(file_record.storage_path):
        raise HTTPException(status_code=404, detail="文件已丢失")

    media_map = {
        "txt": "text/plain; charset=utf-8",
        "md": "text/markdown; charset=utf-8",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }
    return FileResponse(
        path=file_record.storage_path,
        media_type=media_map.get(file_record.file_type, "application/octet-stream"),
        filename=file_record.original_filename,
    )


# ── helper ──────────────────────────────────────────────────────────
def _project_to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        access_token=p.access_token,
        status=p.status,
        input_text=p.input_text,
        image_count=len(p.images) if p.images else 0,
        file_count=len(p.files) if p.files else 0,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )