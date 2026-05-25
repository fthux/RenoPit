"""
Analysis Engine — 分析引擎编排层
流程控制：预处理 → Prompt 构建 → LLM 调用 → JSON 校验 → 结果存储
"""

import asyncio
import base64
import concurrent.futures
import logging
import os
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.analysis import Analysis
from ..models.project import Project
from ..models.project_image import ProjectImage
from ..models.project_file import ProjectFile
from .image_processor import image_to_base64, compress_image
from .file_parser import extract_text as parse_file_text
from .prompt_builder import build_system_prompt
from .llm_service import analyze_design
from .json_validator import validate_and_repair

logger = logging.getLogger(__name__)


class InputValidationError(ValueError):
    """输入校验失败"""
    pass


def _validate_input(
    has_images: bool,
    has_file_texts: bool,
    has_input_text: bool,
) -> None:
    """校验输入：至少需要图片、文件文本或用户补充文本中的一项"""
    if not has_images and not has_file_texts and not has_input_text:
        raise InputValidationError(
            "分析失败：缺少可分析的内容。请至少提供设计图、文本文件或补充说明中的一项。"
        )


def run_analysis_sync(project_id: str) -> dict:
    """同步执行分析（供 Celery 任务调用）

    完整流程：
    1. 加载项目数据（图片、文件、输入文本）
    2. 预处理（图片压缩、文件文本提取）
    3. 输入校验
    4. 构建系统提示词
    5. 调用 LLM 分析
    6. JSON 校验与修复
    7. 结果存储到数据库
    8. 返回结果字典

    Args:
        project_id: 项目 ID

    Returns:
        结果字典：{"status": "completed" | "failed", "analysis_id": str, ...}

    Raises:
        InputValidationError: 输入校验失败
    """
    db: Session = SessionLocal()
    analysis: Optional[Analysis] = None

    try:
        # Step 1: 加载项目
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 加载图片
        images = db.query(ProjectImage).filter(
            ProjectImage.project_id == project_id,
        ).all()

        # 加载文件
        files = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
        ).all()

        # Step 2: 预处理
        logger.info(
            "[AnalysisEngine] 开始预处理 project=%s, images=%d, files=%d, input_text=%s",
            project_id, len(images), len(files),
            "有" if project.input_text else "无",
        )

        # 图片：读取并压缩
        images_base64: list[str] = []
        for img in images:
            file_path = img.storage_path
            if os.path.exists(file_path):
                try:
                    # 先压缩大图，再转 base64
                    compress_image(file_path)
                    b64 = image_to_base64(file_path)
                    images_base64.append(b64)
                except Exception:
                    # 单张图片失败不阻断整个分析
                    continue

        # 文件：提取文本
        extracted_texts: list[str] = []
        for f in files:
            file_path = f.storage_path
            if os.path.exists(file_path):
                try:
                    # 根据文件扩展名确定类型
                    ext = os.path.splitext(f.original_filename)[1].lstrip(".").lower()
                    text = parse_file_text(file_path, ext)
                    if text:
                        extracted_texts.append(text)
                        # 更新数据库中的 extracted_text
                        f.extracted_text = text
                        db.add(f)
                except Exception:
                    continue

        # 用户补充文本
        input_text = project.input_text

        logger.info(
            "[AnalysisEngine] 预处理完成 project=%s, valid_images=%d, extracted_texts=%d",
            project_id, len(images_base64), len(extracted_texts),
        )

        # Step 3: 输入校验
        _validate_input(
            has_images=len(images_base64) > 0,
            has_file_texts=len(extracted_texts) > 0,
            has_input_text=bool(input_text and input_text.strip()),
        )

        # 创建 Analysis 记录（状态：processing）
        analysis = Analysis(
            project_id=project_id,
            status="processing",
        )
        db.add(analysis)
        db.flush()  # 获取 analysis.id

        logger.info(
            "[AnalysisEngine] 开始 LLM 分析 analysis_id=%s, provider=%s",
            analysis.id, settings.AI_MODEL_PROVIDER,
        )

        # Step 4: 构建系统提示词
        system_prompt = build_system_prompt(settings.ENABLE_WEB_SEARCH)

        # Step 5: 调用 LLM（同步包装异步调用）
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已运行的事件循环中（如 Celery 使用了 asyncio）
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    llm_response = executor.submit(
                        lambda: asyncio.run(
                            analyze_design(
                                images_base64=images_base64,
                                extracted_texts=extracted_texts if extracted_texts else None,
                                input_text=input_text,
                                system_prompt=system_prompt,
                            )
                        )
                    ).result()
            else:
                llm_response = loop.run_until_complete(
                    analyze_design(
                        images_base64=images_base64,
                        extracted_texts=extracted_texts if extracted_texts else None,
                        input_text=input_text,
                        system_prompt=system_prompt,
                    )
                )
        except RuntimeError:
            # 没有事件循环
            llm_response = asyncio.run(
                analyze_design(
                    images_base64=images_base64,
                    extracted_texts=extracted_texts if extracted_texts else None,
                    input_text=input_text,
                    system_prompt=system_prompt,
                )
            )

        logger.info(
            "[AnalysisEngine] LLM 响应长度=%d",
            len(llm_response) if llm_response else 0,
        )

        # 记录 LLM 原始响应的前500字以便调试
        if llm_response:
            logger.info(
                "[AnalysisEngine] LLM 响应预览: %s",
                llm_response,
            )
        else:
            logger.error("[AnalysisEngine] LLM 返回空响应，完整流程将失败")

        # Step 6: JSON 校验与修复
        result_data, error_msg = validate_and_repair(llm_response)

        # Step 7: 存储结果
        if result_data is not None:
            analysis.raw_result_json = result_data
            analysis.status = "completed"
            analysis.completed_at = datetime.utcnow()
            logger.info(
                "[AnalysisEngine] 分析完成 analysis_id=%s, problems=%d",
                analysis.id,
                len(result_data.get("problems", [])),
            )
        else:
            analysis.error_message = error_msg or "JSON 校验失败"
            analysis.status = "failed"
            analysis.completed_at = datetime.utcnow()
            logger.error(
                "[AnalysisEngine] JSON 校验失败 analysis_id=%s: %s",
                analysis.id, error_msg,
            )

        db.commit()
        db.refresh(analysis)

        return {
            "status": analysis.status,
            "analysis_id": analysis.id,
            "project_id": project_id,
            "problems_count": len(result_data.get("problems", [])) if result_data else 0,
            "error_message": analysis.error_message,
        }

    except InputValidationError as e:
        # 输入校验失败
        logger.warning("[AnalysisEngine] 输入校验失败 project=%s: %s", project_id, e)
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.utcnow()
            db.commit()

        return {
            "status": "failed",
            "project_id": project_id,
            "error_message": str(e),
        }

    except Exception as e:
        logger.error(
            "[AnalysisEngine] 分析异常 project=%s: %s",
            project_id, str(e),
        )
        db.rollback()

        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.utcnow()
            db.commit()

        return {
            "status": "failed",
            "project_id": project_id,
            "error_message": str(e),
        }

    finally:
        db.close()


def run_document_analysis_sync(project_id: str, project_file_id: str) -> dict:
    """同步执行文档分析（合同/报价单审核），供 Celery 任务调用

    完整流程：
    1. 加载项目文件并提取文本
    2. 文档分类检测（合同/报价单/无关文件）
    3. 调用 LLM 进行合同/报价审核
    4. JSON 校验与修复
    5. 结果存储到 document_analyses 表
    6. 返回结果字典

    Args:
        project_id: 项目 ID
        project_file_id: 要分析的文件 ID

    Returns:
        结果字典：{"status": "completed" | "failed", "analysis_id": str, ...}
    """
    from ..models.document_analysis import DocumentAnalysis
    from .document_classifier import classify_document
    from .llm_service import analyze_document

    db: Session = SessionLocal()
    doc_analysis: Optional[DocumentAnalysis] = None

    try:
        # Step 1: 加载项目文件
        project_file = db.query(ProjectFile).filter(
            ProjectFile.id == project_file_id,
            ProjectFile.project_id == project_id,
        ).first()

        if not project_file:
            raise ValueError(f"项目文件不存在: project={project_id}, file={project_file_id}")

        file_path = project_file.storage_path
        if not os.path.exists(file_path):
            raise ValueError(f"文件实体不存在: {file_path}")

        logger.info(
            "[AnalysisEngine] 开始文档分析 project=%s, file=%s, name=%s",
            project_id, project_file_id, project_file.original_filename,
        )

        # Step 2: 提取文本
        ext = os.path.splitext(project_file.original_filename)[1].lstrip(".").lower()
        document_text = parse_file_text(file_path, ext)

        if not document_text or not document_text.strip():
            raise ValueError("文件内容为空或无法提取文本")

        logger.info(
            "[AnalysisEngine] 文档文本提取完成: len=%d",
            len(document_text),
        )

        # 更新文件记录的 extracted_text
        project_file.extracted_text = document_text
        db.add(project_file)
        db.flush()

        # Step 3: 文档分类
        classification = classify_document(document_text, project_file.original_filename)

        logger.info(
            "[AnalysisEngine] 文档分类完成: type=%s, confidence=%.2f, relevant=%s",
            classification.doc_type, classification.confidence, classification.is_relevant,
        )

        # Step 4: 创建 DocumentAnalysis 记录
        doc_analysis = DocumentAnalysis(
            project_id=project_id,
            project_file_id=project_file_id,
            status="processing",
            doc_type=classification.doc_type,
            confidence=classification.confidence,
            classifications_json={
                "is_relevant": classification.is_relevant,
                "doc_type": classification.doc_type,
                "language": classification.language,
                "confidence": classification.confidence,
                "reasons": classification.reasons,
                "key_snippets": classification.key_snippets,
                "suggestion": classification.suggestion,
            },
        )
        db.add(doc_analysis)
        db.flush()

        logger.info("[AnalysisEngine] DocumentAnalysis 记录创建: id=%s", doc_analysis.id)

        # Step 5: 调用 LLM 分析
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    llm_response = executor.submit(
                        lambda: asyncio.run(
                            analyze_document(
                                document_text=document_text,
                                filename=project_file.original_filename,
                            )
                        )
                    ).result()
            else:
                llm_response = loop.run_until_complete(
                    analyze_document(
                        document_text=document_text,
                        filename=project_file.original_filename,
                    )
                )
        except RuntimeError:
            llm_response = asyncio.run(
                analyze_document(
                    document_text=document_text,
                    filename=project_file.original_filename,
                )
            )

        logger.info(
            "[AnalysisEngine] LLM 文档分析响应长度=%d",
            len(llm_response) if llm_response else 0,
        )

        # Step 6: JSON 校验与修复
        from .json_validator import validate_document_report
        result_data, error_msg = validate_document_report(llm_response)

        if result_data is not None:
            doc_analysis.risks_json = result_data
            doc_analysis.summary = result_data.get("summary", "")
            doc_analysis.total_estimated_risk = result_data.get("total_estimated_risk", "")
            doc_analysis.risks_count = len(result_data.get("risks", []))
            doc_analysis.status = "completed"
            doc_analysis.completed_at = datetime.utcnow()
            logger.info(
                "[AnalysisEngine] 文档分析完成: risks=%d, summary=%s",
                doc_analysis.risks_count,
                doc_analysis.summary[:100] if doc_analysis.summary else "",
            )

            # Step 6.5: 增项预测（仅在报价单分析时触发）
            if classification.doc_type == "quotation":
                try:
                    logger.info(
                        "[AnalysisEngine] 开始增项预测: project=%s, file=%s",
                        project_id, project_file_id,
                    )
                    from .llm_service import predict_extra_items
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            pred_response = executor.submit(
                                lambda: asyncio.run(
                                    predict_extra_items(result_data)
                                )
                            ).result()
                    else:
                        pred_response = loop.run_until_complete(
                            predict_extra_items(result_data)
                        )
                    # 解析预测结果（使用 parse_json 处理 markdown 围栏等）
                    from .json_validator import parse_json
                    pred_data, parse_err = parse_json(pred_response)
                    if pred_data is not None:
                        # 将预测结果存入 risks_json 中，供后续读取
                        # 使用 copy 确保 SQLAlchemy 能检测到 JSON column 变更
                        result_data_copy = dict(result_data)
                        result_data_copy["extra_item_prediction"] = pred_data
                        doc_analysis.risks_json = result_data_copy
                        logger.info(
                            "[AnalysisEngine] 增项预测完成: items=%d, predicted_total=%s",
                            len(pred_data.get("predicted_items", [])),
                            pred_data.get("predicted_actual_total", "N/A"),
                        )
                    else:
                        logger.warning(
                            "[AnalysisEngine] 增项预测 JSON 解析失败: %s",
                            parse_err,
                        )
                except Exception as pred_err:
                    logger.warning(
                        "[AnalysisEngine] 增项预测失败（不影响主流程）: %s",
                        str(pred_err),
                    )
            else:
                logger.info(
                    "[AnalysisEngine] 文档类型为 %s，跳过增项预测",
                    classification.doc_type,
                )
        else:
            doc_analysis.error_message = error_msg or "JSON 校验失败"
            doc_analysis.status = "failed"
            doc_analysis.completed_at = datetime.utcnow()
            logger.error(
                "[AnalysisEngine] 文档 JSON 校验失败: %s", error_msg,
            )

        db.commit()
        db.refresh(doc_analysis)

        return {
            "status": doc_analysis.status,
            "analysis_id": doc_analysis.id,
            "project_id": project_id,
            "project_file_id": project_file_id,
            "doc_type": doc_analysis.doc_type,
            "confidence": doc_analysis.confidence,
            "risks_count": doc_analysis.risks_count,
            "summary": doc_analysis.summary,
            "total_estimated_risk": doc_analysis.total_estimated_risk,
            "error_message": doc_analysis.error_message,
        }

    except Exception as e:
        logger.error(
            "[AnalysisEngine] 文档分析异常 project=%s, file=%s: %s",
            project_id, project_file_id, str(e),
        )
        db.rollback()

        if doc_analysis:
            doc_analysis.status = "failed"
            doc_analysis.error_message = str(e)
            doc_analysis.completed_at = datetime.utcnow()
            db.commit()

        return {
            "status": "failed",
            "project_id": project_id,
            "project_file_id": project_file_id,
            "error_message": str(e),
        }

    finally:
        db.close()
