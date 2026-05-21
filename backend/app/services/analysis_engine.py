"""
Analysis Engine — 分析引擎编排层
流程控制：预处理 → Prompt 构建 → LLM 调用 → JSON 校验 → 结果存储
"""

import base64
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
            ProjectImage.deleted_at.is_(None),
        ).all()

        # 加载文件
        files = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.deleted_at.is_(None),
        ).all()

        # Step 2: 预处理
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
                    ext = os.path.splitext(f.original_name)[1].lstrip(".").lower()
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

        # Step 4: 构建系统提示词
        system_prompt = build_system_prompt(settings.ENABLE_WEB_SEARCH)

        # Step 5: 调用 LLM（同步包装异步调用）
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已运行的事件循环中（如 Celery 使用了 asyncio）
                import concurrent.futures
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

        # Step 6: JSON 校验与修复
        result_data, error_msg = validate_and_repair(llm_response)

        # Step 7: 存储结果
        if result_data is not None:
            analysis.raw_result_json = result_data
            analysis.status = "completed"
            analysis.completed_at = datetime.utcnow()
        else:
            analysis.error_message = error_msg or "JSON 校验失败"
            analysis.status = "failed"
            analysis.completed_at = datetime.utcnow()

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