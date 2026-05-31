"""
Celery 分析任务 — 异步执行 AI 分析并通过 SSE 推送状态变更
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional

from .celery_app import celery_app
from ..core.database import SessionLocal
from ..models.project import Project
from ..models.analysis import Analysis
from ..models.project_file import ProjectFile
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
    3. 调用 analysis_engine.run_analysis_sync() 执行设计图分析
    4. 无论设计图分析成功还是失败，自动查询项目中的可分析文件（PDF/docx/txt/md），
       对每个文件自动调用 run_document_analysis_sync() 执行文档分析
       （文档分析独立于设计图分析，避免因图片上传导致纯文本 LLM 报错而阻断后续流程）
    5. 多文档交叉核查（当有 ≥ 2 份文本文件时自动触发）
    6. 根据分析结果推送 SSE + 更新项目状态
       — 设计图分析成功 或 文档分析任一成功 → completed
       — 均失败 → failed

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

        # Step 3: 执行设计图分析（可能因纯文本 LLM 不支持图片而失败）
        logger.info(f"Starting design analysis for project={project_id}")
        try:
            result = run_analysis_sync(project_id)
        except Exception as e:
            logger.error("Design analysis failed: %s", str(e))
            result = {"status": "failed", "error_message": str(e)}

        # Step 4: 自动执行文档分析（合同/报价单）
        # 无论设计图分析成功还是失败，文档分析都应独立执行，
        # 避免因图片上传导致纯文本 LLM 报错而阻断后续文档分析
        doc_results: list[dict] = []
        try:
            # 查询项目中已提取文本的可分析文件
            analyzable_files = db.query(ProjectFile).filter(
                ProjectFile.project_id == project_id,
                ProjectFile.extracted_text.isnot(None),
                ProjectFile.extracted_text != "",
                ProjectFile.file_type.in_(["pdf", "docx", "txt", "md"]),
            ).all()

            if analyzable_files:
                logger.info(
                    "Found %d analyzable files for document analysis",
                    len(analyzable_files),
                )
                for pf in analyzable_files:
                    try:
                        doc_result = run_document_analysis_sync(project_id, pf.id)
                        doc_results.append(doc_result)
                        logger.info(
                            "Document analysis for file %s: %s",
                            pf.id, doc_result.get("status"),
                        )
                    except Exception as e:
                        logger.error(
                            "Document analysis failed for file %s: %s",
                            pf.id, str(e),
                        )
                        doc_results.append({
                            "status": "failed",
                            "project_file_id": pf.id,
                            "error_message": str(e),
                        })
        except Exception as e:
            logger.error(
                "Error querying project files for document analysis: %s",
                str(e),
            )

        # Step 5: 多文档交叉核查（当有 ≥ 2 份文本文件时自动触发）
        cross_check_result: Optional[dict] = None
        if len(doc_results) >= 2:
            try:
                from ..services.analysis_engine import run_cross_check_sync
                logger.info(
                    "Starting cross-document check for project=%s (doc_count=%d)",
                    project_id, len(doc_results),
                )
                cross_check_result = run_cross_check_sync(project_id)
                logger.info(
                    "Cross-document check completed for project=%s: %s",
                    project_id, cross_check_result.get("status"),
                )
            except Exception as e:
                logger.error(
                    "Cross-document check failed for project=%s: %s",
                    project_id, str(e),
                )

        # Step 6: 根据结果推送 SSE + 更新项目状态
        design_ok = result.get("status") == "completed"
        doc_ok_count = sum(1 for r in doc_results if r.get("status") == "completed")
        doc_total = len(doc_results)

        # 只要设计图分析或文档分析任一成功，项目即视为完成
        if design_ok or doc_ok_count > 0:
            # 统计设计图分析结果
            design_message = f"发现 {result.get('problems_count', 0)} 个问题" if design_ok else "设计图分析失败（已跳过）"

            # 统计文档分析结果
            doc_message = ""
            if doc_total > 0:
                doc_message = f"，合同/报价单分析完成 {doc_ok_count}/{doc_total}"

            # 交叉核查信息
            cross_check_message = ""
            if cross_check_result and cross_check_result.get("status") == "completed":
                dc = cross_check_result.get("discrepancies_count", 0)
                cross_check_message = f"，发现 {dc} 项跨文档不一致" if dc > 0 else "，未发现跨文档不一致"

            _update_project_status(db, project_id, "completed")
            _publish_sse(project_id, "status_change", {
                "project_id": project_id,
                "status": "completed",
                "message": f"分析完成：{design_message}{doc_message}{cross_check_message}",
                "problems_count": result.get("problems_count", 0) + doc_ok_count,
                "timestamp": datetime.utcnow().isoformat(),
            })
        else:
            # 设计图分析和文档分析均失败
            error_details = []
            if not design_ok:
                error_details.append(f"设计图: {result.get('error_message', '未知错误')}")
            if doc_total > 0 and doc_ok_count == 0:
                error_details.append(f"文档分析: {doc_total} 个文件均失败")
            detail_str = "；".join(error_details)

            _update_project_status(db, project_id, "failed")
            _publish_sse(project_id, "status_change", {
                "project_id": project_id,
                "status": "failed",
                "message": f"分析失败：{detail_str}" if detail_str else "分析失败",
                "timestamp": datetime.utcnow().isoformat(),
            })

        logger.info(
            "Analysis completed for project=%s: design=%s, doc_analyses=%d",
            project_id, result.get("status"), len(doc_results),
        )
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