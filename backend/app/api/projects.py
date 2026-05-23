"""
Project API — matches frontend routes at /api/projects/*
"""

import asyncio
import logging
import os
import secrets
import uuid
from datetime import datetime
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


# ── POST /api/projects — create project (JSON body only) ────────────
@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreateRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Create a new project from JSON body.
    Files are uploaded separately via POST /api/projects/{id}/upload.
    """
    project = Project(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        access_token=_generate_access_token(),
        status="pending",
        input_text=body.input_text,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(f"Project created: id={project.id}, name={project.name}, input_text={'yes' if body.input_text else 'no'}")
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


# ── POST /api/projects/:id/stop — stop analysis ────────────────────
@router.post("/{project_id}/stop")
async def stop_analysis(project_id: str, db: Session = Depends(get_db)):
    """停止正在分析的项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if project.status != "analyzing":
        raise HTTPException(status_code=409, detail="项目未在分析中")

    project.status = "pending"
    project.updated_at = datetime.utcnow()

    # 标记最近的 analyzing/pending analysis 为 failed
    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id, Analysis.status.in_(["processing", "pending"]))
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if analysis:
        analysis.status = "failed"
        analysis.error_message = "用户手动停止"
        analysis.completed_at = datetime.utcnow()

    db.commit()
    logger.info(f"Analysis stopped for project={project_id}")
    return {"detail": "ok", "status": "pending"}


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
        .filter(Analysis.project_id == project_id)
        .order_by(Analysis.completed_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果尚未生成")

    # 如果分析失败，仍然返回 analysis 记录，包含 error_message
    if analysis.status == "failed":
        return AnalysisResponse(
            id=analysis.id,
            project_id=analysis.project_id,
            status=analysis.status,
            problems_count=0,
            result_json=None,
            error_message=analysis.error_message,
            completed_at=analysis.completed_at,
            created_at=analysis.created_at,
        )

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


# ── POST /api/projects/:id/analyze — trigger analysis ─────────────
@router.post("/{project_id}/analyze")
async def trigger_analysis(project_id: str, db: Session = Depends(get_db)):
    """启动分析任务（Celery 异步执行）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已有可分析的内容
    from ..services.analysis_engine import _validate_input
    images = db.query(ProjectImage).filter(
        ProjectImage.project_id == project_id,
    ).all()
    files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
    ).all()
    has_images = len(images) > 0
    has_files = len(files) > 0
    has_input_text = bool(project.input_text and project.input_text.strip())

    try:
        _validate_input(has_images=has_images, has_file_texts=has_files, has_input_text=has_input_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if project.status == "analyzing":
        raise HTTPException(status_code=409, detail="正在分析中，请稍候")

    # 更新状态 → analyzing
    project.status = "analyzing"
    project.updated_at = datetime.utcnow()
    db.commit()

    # 入队 Celery 任务
    try:
        from ..tasks.analysis import run_analysis_task
        run_analysis_task.delay(project_id)
        logger.info(f"Analysis task enqueued for project={project_id}")
    except Exception as e:
        logger.error(f"Failed to enqueue analysis task: {e}")
        project.status = "pending"
        db.commit()
        raise HTTPException(status_code=500, detail=f"无法启动分析任务: {e}")

    return {"detail": "ok", "status": "analyzing"}


# ── GET /api/projects/:id/analyze/stream — SSE via DB polling ─────
@router.get("/{project_id}/analyze/stream")
async def stream_analysis(project_id: str):
    """
    SSE 端点：轮询数据库状态并推送事件。
    使用 DB 轮询而非内存队列，确保 Celery worker 写入的状态能被 SS 端点读到。
    """
    import json as json_module
    from ..core.database import SessionLocal
    from ..models.analysis import Analysis as AnalysisModel
    from ..models.analysis import Analysis

    async def event_generator():
        sse_db = SessionLocal()
        logger.info(f"SSE stream started for project={project_id}")
        try:
            project = sse_db.query(Project).filter(Project.id == project_id).first()
            if not project:
                yield f"event: failed\ndata: {json_module.dumps({'error': '项目不存在'}, ensure_ascii=False)}\n\n"
                return

            last_status = project.status
            logger.info(f"SSE initial status: project={project_id}, status={last_status}")

            # 发送连接确认
            yield f"event: progress\ndata: {json_module.dumps({'progress': 5, 'message': '正在连接 AI 服务...'}, ensure_ascii=False)}\n\n"

            # 轮询状态变化，带渐进进度
            retry_count = 0
            max_retries = 150  # 5 minutes max (150 * 2s)
            # 模拟渐进进度 (10% ~ 85% 之间平滑推进)
            simulated_progress = 10
            while last_status in ("analyzing", "parsing"):
                await asyncio.sleep(2)
                retry_count += 1
                if retry_count > max_retries:
                    yield f"event: failed\ndata: {json_module.dumps({'error': '分析超时，请重试'}, ensure_ascii=False)}\n\n"
                    return

                sse_db.refresh(project)
                if project.status != last_status:
                    logger.info(f"SSE status change: project={project_id}, {last_status} → {project.status}")
                    last_status = project.status
                    if last_status == "analyzing":
                        yield f"event: progress\ndata: {json_module.dumps({'progress': 30, 'message': 'AI 分析中，正在识别设计元素...'}, ensure_ascii=False)}\n\n"
                        simulated_progress = 30
                    elif last_status == "completed":
                        yield f"event: progress\ndata: {json_module.dumps({'progress': 95, 'message': '正在保存结果...'}, ensure_ascii=False)}\n\n"
                    elif last_status == "failed":
                        # 从 Analysis 表中读取实际错误信息（按 created_at 降序取最新记录）
                        analysis = sse_db.query(Analysis).filter(
                            Analysis.project_id == project_id,
                        ).order_by(Analysis.created_at.desc()).first()
                        error_detail = analysis.error_message if analysis and analysis.error_message else '分析失败，请查看详情'
                        logger.warning(f"SSE analysis failed for project={project_id}: {error_detail}")
                        yield f"event: failed\ndata: {json_module.dumps({'error': error_detail, 'error_detail': error_detail}, ensure_ascii=False)}\n\n"
                        return
                else:
                    # 状态未变化，渐进推进进度条（给用户一种"正在运行"的感觉）
                    if simulated_progress < 85:
                        simulated_progress += 2
                        # 不同阶段给出不同消息
                        stage_messages = {
                            10: "正在加载设计图...",
                            20: "AI 开始分析...",
                            35: "正在检查卫生死角...",
                            45: "正在评估空间布局...",
                            55: "正在排查实用性陷阱...",
                            65: "正在评估隐性成本...",
                            75: "正在检查安全隐患...",
                            85: "正在生成分析报告...",
                        }
                        # 找到最接近的 stage 消息
                        message = "AI 分析中，请稍候..."
                        for stage, msg in sorted(stage_messages.items()):
                            if simulated_progress >= stage:
                                message = msg
                        yield f"event: progress\ndata: {json_module.dumps({'progress': simulated_progress, 'message': message}, ensure_ascii=False)}\n\n"

            # 最终状态
            if last_status == "completed":
                yield f"event: completed\ndata: {json_module.dumps({'progress': 100, 'message': '分析完成！正在跳转报告...'}, ensure_ascii=False)}\n\n"
                logger.info(f"SSE completed for project={project_id}")
            elif last_status == "failed":
                # 从 Analysis 表中读取实际错误信息（按 created_at 降序取最新记录）
                analysis = sse_db.query(Analysis).filter(
                    Analysis.project_id == project_id,
                ).order_by(Analysis.created_at.desc()).first()
                error_detail = analysis.error_message if analysis and analysis.error_message else '分析失败'
                logger.warning(f"SSE analysis final failed for project={project_id}: {error_detail}")
                yield f"event: failed\ndata: {json_module.dumps({'error': error_detail, 'error_detail': error_detail}, ensure_ascii=False)}\n\n"
            elif last_status == "pending":
                yield f"event: stopped\ndata: {json_module.dumps({'message': '分析已停止'}, ensure_ascii=False)}\n\n"
                logger.info(f"SSE stopped for project={project_id}")

        except Exception as e:
            logger.exception(f"SSE stream error for project={project_id}: {e}")
            yield f"event: failed\ndata: {json_module.dumps({'error': f'连接异常: {str(e)}'}, ensure_ascii=False)}\n\n"
        finally:
            sse_db.close()
            logger.info(f"SSE stream closed for project={project_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── GET /api/projects/:id/result — frontend-oriented analysis result ──
@router.get("/{project_id}/result")
async def get_analysis_result(project_id: str, db: Session = Depends(get_db)):
    """返回前端友好的分析结果格式，将 AI JSON 转换为前端 types 定义的结构。

    转换规则：
    - problems → pitfalls（每个问题扁平化为 {id, category, description, severity, location, suggestion}）
    - summary → {total_pitfalls, critical_count, high_count, medium_count, low_count, score, summary_text}
    - 严重等级按 heuristic 从 critique 文本匹配判断
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    analysis = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果尚未生成")

    # 失败时返回 error_message
    if analysis.status == "failed":
        return {
            "id": analysis.id,
            "project_id": project_id,
            "status": "failed",
            "summary": {
                "total_pitfalls": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "score": 0,
                "summary_text": analysis.error_message or "分析失败",
            },
            "pitfalls": [],
            "error_message": analysis.error_message,
            "completed_at": analysis.completed_at,
            "created_at": analysis.created_at,
        }

    raw_data = analysis.raw_result_json or {}
    problems = raw_data.get("problems", [])
    summary_text = raw_data.get("summary", "")

    # 转换 summary
    score = _calculate_score(len(problems))
    severity_counts = _count_severities(problems)

    # 转换 problems → pitfalls
    pitfalls = []
    for i, p in enumerate(problems):
        if not isinstance(p, dict):
            continue
        severity = _infer_severity(p)
        pitfalls.append({
            "id": str(i + 1),
            "category": _infer_category(p),
            "description": p.get("title", p.get("critique", "")),
            "severity": severity,
            "location": p.get("location"),
            "suggestion": p.get("alternative", ""),
            "critique": p.get("critique"),
            "trap_explanation": p.get("trap_explanation"),
            "bbox": p.get("bbox"),
        })

    return {
        "id": analysis.id,
        "project_id": project_id,
        "status": "completed",
        "summary": {
            "total_pitfalls": len(pitfalls),
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "score": score,
            "summary_text": summary_text,
        },
        "pitfalls": pitfalls,
        "error_message": None,
        "completed_at": analysis.completed_at,
        "created_at": analysis.created_at,
    }


def _calculate_score(problem_count: int) -> int:
    """根据问题数量估算评分 (0-100)"""
    if problem_count == 0:
        return 95
    score = max(0, 100 - problem_count * 8)
    return score


def _count_severities(problems: list) -> dict:
    """统计严重等级"""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for p in problems:
        sev = _infer_severity(p)
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _infer_severity(problem: dict) -> str:
    """从问题文本推断严重等级"""
    title = (problem.get("title") or "").lower()
    critique = (problem.get("critique") or "").lower()
    combined = title + " " + critique

    # 严重关键词
    critical_kw = ["安全", "坠落", "坍塌", "火灾", "漏电", "中毒", "危险", "致命"]
    high_kw = ["高额", "坑", "陷阱", "浪费", "无法", "严重", "重大"]
    medium_kw = ["不便", "麻烦", "难看", "不佳", "较差", "一般"]
    low_kw = ["微", "略", "稍", "可能", "可接受"]

    for kw in critical_kw:
        if kw in combined:
            return "critical"
    for kw in high_kw:
        if kw in combined:
            return "high"
    for kw in medium_kw:
        if kw in combined:
            return "medium"
    for kw in low_kw:
        if kw in combined:
            return "low"
    return "medium"  # default


def _infer_category(problem: dict) -> str:
    """从问题文本推断类别"""
    title = (problem.get("title") or "").lower()
    critique = (problem.get("critique") or "").lower()
    combined = title + " " + critique
    location = (problem.get("location") or "").lower()

    category_map = [
        ("卫生死角", ["积灰", "清洁", "卫生", "死角"]),
        ("空间压迫", ["压抑", "压迫", "拥挤", "空间小", "狭小"]),
        ("安全与健康", ["安全", "坠落", "坍塌", "火灾", "漏电", "中毒"]),
        ("隐性成本", ["成本", "费用", "预算", "价格", "高价", "溢价", "浪费"]),
        ("实用性伪需求", ["不实用", "伪", "好看", "美观", "装饰", "鸡肋"]),
    ]

    for category, keywords in category_map:
        for kw in keywords:
            if kw in combined or kw in location:
                return category
    return "其他"


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
    problems = result.get("problems", [])
    raw_summary = result.get("summary", {})

    # Normalize summary: LLM output may be a string (old prompt) or dict
    if isinstance(raw_summary, dict):
        by_severity = raw_summary.get("by_severity", {})
        if not isinstance(by_severity, dict):
            by_severity = {}
        summary = {
            "total_pitfalls": raw_summary.get("total_pitfalls", raw_summary.get("total", len(problems))),
            "critical_count": raw_summary.get("critical_count", by_severity.get("critical", 0)),
            "high_count": raw_summary.get("high_count", by_severity.get("high", 0)),
            "medium_count": raw_summary.get("medium_count", by_severity.get("medium", 0)),
            "low_count": raw_summary.get("low_count", by_severity.get("low", 0)),
            "score": raw_summary.get("score", 0),
            "summary_text": raw_summary.get("overall_assessment", ""),
        }
    else:
        # summary is a string (old prompt) - derive stats from problems
        sev_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for p in problems:
            sev = p.get("severity", "low")
            if sev in sev_count:
                sev_count[sev] += 1
        score = max(0, min(100, 100 - sum(
            sev_count[s] * w for s, w in [("critical", 15), ("high", 8), ("medium", 3), ("low", 1)]
        )))
        summary = {
            "total_pitfalls": len(problems),
            "critical_count": sev_count["critical"],
            "high_count": sev_count["high"],
            "medium_count": sev_count["medium"],
            "low_count": sev_count["low"],
            "score": score,
            "summary_text": raw_summary if isinstance(raw_summary, str) else "",
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