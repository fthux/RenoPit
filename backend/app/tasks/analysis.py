"""
Celery 分析任务 — 异步执行 AI 分析并通过 SSE 推送状态变更
"""

import logging
import asyncio
from datetime import datetime

from .celery_app import celery_app
from ..core.database import SessionLocal
from ..models.project import Project
from ..models.analysis import Analysis
from ..services.analysis_engine import run_analysis_sync, run_document_analysis_sync, InputValidationError
from ..services.sse_manager import sse_manager

logger = logging.getLogger(__name__)


def _update_project_status(db, project_id: str, status: str):
    """更新项目状态并提交"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.status = status
        project.updated_at = datetime.utcnow()
        db.commit()


def _publish_sse(project_id: str, event: str, data: dict):
    """通过 SSE 管理器推送事件"""
    try:
        sse_manager.publish(project_id, event, data)
    except Exception as e:
        logger.warning(f"SSE publish failed for project={project_id}: {e}")


@celery_app.task(bind=True, max_retries=0)
def run_analysis_task(self, project_id: str):
    """Celery 任务：执行完整分析流程

    流程：
    1. 更新项目状态为 analyzing
    2. 推送 SSE: status_change → analyzing
    3. 调用 analysis_engine.run_analysis_sync()
    4. 推送 SSE: status_change → completed/failed
    5. 更新项目状态

    Args:
        project_id: 项目 ID
    """
    db = SessionLocal()

    try:
        # Step 1: 验证项目存在
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project not found: {project_id}")
            return {"status": "failed", "error": "Project not found"}

        # Step 2: 更新状态 → analyzing
        _update_project_status(db, project_id, "analyzing")
        _publish_sse(project_id, "status_change", {
            "project_id": project_id,
            "status": "analyzing",
            "message": "AI 分析中，请稍候...",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Step 3: 执行分析
        logger.info(f"Starting analysis for project={project_id}")
        result = run_analysis_sync(project_id)

        # Step 4: 根据结果推送 SSE + 更新项目状态
        if result.get("status") == "completed":
            _update_project_status(db, project_id, "completed")
            _publish_sse(project_id, "status_change", {
                "project_id": project_id,
                "status": "completed",
                "message": f"分析完成，发现 {result.get('problems_count', 0)} 个问题",
                "problems_count": result.get("problems_count", 0),
                "timestamp": datetime.utcnow().isoformat(),
            })
        else:
            _update_project_status(db, project_id, "failed")
            _publish_sse(project_id, "status_change", {
                "project_id": project_id,
                "status": "failed",
                "message": result.get("error_message", "分析失败"),
                "timestamp": datetime.utcnow().isoformat(),
            })

        logger.info(f"Analysis completed for project={project_id}: {result.get('status')}")
        return result

    except InputValidationError as e:
        # 输入校验失败
        _update_project_status(db, project_id, "failed")
        _publish_sse(project_id, "status_change", {
            "project_id": project_id,
            "status": "failed",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {"status": "failed", "error": str(e)}

    except Exception as e:
        logger.exception(f"Analysis failed for project={project_id}")
        _update_project_status(db, project_id, "failed")
        _publish_sse(project_id, "status_change", {
            "project_id": project_id,
            "status": "failed",
            "message": f"分析过程出错: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {"status": "failed", "error": str(e)}

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=0)
def run_document_analysis_task(self, project_id: str, project_file_id: str):
    """Celery 任务：执行合同/报价单文档分析

    流程：
    1. 调用 analysis_engine.run_document_analysis_sync()
    2. 推送 SSE: status_change → completed/failed

    Args:
        project_id: 项目 ID
        project_file_id: 要分析的文件 ID
    """
    try:
        logger.info(
            "Starting document analysis for project=%s, file=%s",
            project_id, project_file_id,
        )
        result = run_document_analysis_sync(project_id, project_file_id)

        if result.get("status") == "completed":
            _publish_sse(project_id, "document_analysis_complete", {
                "project_id": project_id,
                "project_file_id": project_file_id,
                "status": "completed",
                "message": f"文档分析完成，发现 {result.get('risks_count', 0)} 个风险点",
                "risks_count": result.get("risks_count", 0),
                "timestamp": datetime.utcnow().isoformat(),
            })
        else:
            _publish_sse(project_id, "document_analysis_complete", {
                "project_id": project_id,
                "project_file_id": project_file_id,
                "status": "failed",
                "message": result.get("error_message", "文档分析失败"),
                "timestamp": datetime.utcnow().isoformat(),
            })

        logger.info(
            "Document analysis completed for file=%s: %s",
            project_file_id, result.get("status"),
        )
        return result

    except Exception as e:
        logger.exception(
            "Document analysis failed for project=%s, file=%s",
            project_id, project_file_id,
        )
        _publish_sse(project_id, "document_analysis_complete", {
            "project_id": project_id,
            "project_file_id": project_file_id,
            "status": "failed",
            "message": f"文档分析过程出错: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        return {"status": "failed", "error": str(e)}
