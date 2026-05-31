"""
LLM Service — 多模态大模型调用服务
支持 OpenAI SDK 兼容接口（LLM_API_KEY + LLM_BASE_URL + LLM_MODEL_NAME）
"""

import asyncio
import base64
import logging
import time
from typing import Optional

from openai import AsyncOpenAI

from ..core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# 常量
# ============================================================

# 重试配置
MAX_RETRIES = 2
BASE_DELAY = 2  # 秒，指数退避：2s → 4s
TIMEOUT_SECONDS = 180


# ============================================================
# OpenAI SDK 客户端（延迟初始化）
# ============================================================

_openai_client: Optional[AsyncOpenAI] = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=TIMEOUT_SECONDS,
        )
    return _openai_client


# ============================================================
# 工具定义
# ============================================================

# OpenAI 原生 web_search 工具定义
# 注意：仅 OpenAI 官方 API 支持 tools 参数，Gemini/DeepSeek/Ollama 等兼容端点均不支持
WEB_SEARCH_TOOL_OPENAI = {
    "type": "web_search_preview",
}


def _is_openai_api() -> bool:
    """判断当前 LLM_BASE_URL 是否为真正的 OpenAI API（而非兼容端点）"""
    base_url = settings.LLM_BASE_URL.rstrip("/").lower()
    return "api.openai.com" in base_url


# ============================================================
# LLM 调用（多模态 + 纯文本）
# ============================================================

async def _call_llm(
    system_prompt: str,
    user_message: str,
    images_base64: list[str],
    enable_web_search: bool,
) -> str:
    """调用 LLM 多模态 API（OpenAI SDK 兼容接口）

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息文本
        images_base64: Base64 编码的图片列表（不含 data: URL 前缀）
        enable_web_search: 是否启用联网搜索

    Returns:
        LLM 响应文本

    Raises:
        Exception: API 调用失败时的详细信息
    """
    client = _get_openai_client()

    logger.info(
        "[LLM] 开始构建请求: images=%d, user_message_len=%d, system_prompt_len=%d, web_search=%s",
        len(images_base64), len(user_message or ""), len(system_prompt or ""), enable_web_search,
    )

    # 构建消息内容
    content_parts = []

    # 添加图片
    for i, img_b64 in enumerate(images_base64):
        # 检测 MIME 类型（如果以 data: 开头就提取，否则默认 jpeg）
        if img_b64.startswith("data:image/"):
            header_end = img_b64.find(";base64,")
            if header_end != -1:
                mime_type = img_b64[5:header_end]
                img_data = img_b64[header_end + 8:]
            else:
                mime_type = "image/jpeg"
                img_data = img_b64
        else:
            mime_type = "image/jpeg"
            img_data = img_b64

        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{img_data}",
                "detail": "high",
            },
        })
        logger.info(
            "[LLM] 图片 %d/%d: mime=%s, base64_len=%d",
            i + 1, len(images_base64), mime_type, len(img_data),
        )

    # 添加文本
    content_parts.append({
        "type": "text",
        "text": user_message if user_message else "请分析以上设计图",
    })

    # 构建请求参数
    # 仅真正的 OpenAI API 支持 tools 参数（web_search_preview），
    # Gemini/DeepSeek/Ollama 等兼容端点均不支持，跳过以免 400 错误
    tools: Optional[list] = None
    if enable_web_search and _is_openai_api():
        tools = [WEB_SEARCH_TOOL_OPENAI]
        logger.info("[LLM] 已启用联网搜索工具 (OpenAI API)")
    elif enable_web_search:
        logger.info("[LLM] 请求了联网搜索但当前非 OpenAI API，跳过 tools 参数（联网提示已包含在 prompt 中）")

    logger.info("[LLM] 正在发送请求到 API (model=%s)...", settings.LLM_MODEL_NAME)

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_parts},
            ],
            tools=tools,
            max_tokens=65536,
            temperature=0.3,  # 低温度提高一致性
        )

        result = response.choices[0].message.content or ""
        logger.info(
            "[LLM] API 调用成功: response_len=%d, finish_reason=%s",
            len(result),
            response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else 'unknown',
        )

        # 记录是否有工具调用（联网搜索）
        if response.choices[0].message.tool_calls:
            logger.info(
                "[LLM] 模型使用了工具调用: %d 个工具",
                len(response.choices[0].message.tool_calls),
            )

        return result
    except Exception as e:
        logger.error(
            "[LLM] API 调用异常: %s (type=%s)",
            str(e), type(e).__name__,
        )
        raise


async def _call_llm_text(
    system_prompt: str,
    user_message: str,
) -> str:
    """调用 LLM 纯文本分析"""
    client = _get_openai_client()
    logger.info("[LLM-Text] 开始请求, user_message_len=%d", len(user_message))

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=65536,
            temperature=0.3,
        )
        result = response.choices[0].message.content or ""
        logger.info("[LLM-Text] 调用成功: response_len=%d", len(result))
        return result
    except Exception as e:
        logger.error("[LLM-Text] 调用异常: %s", str(e))
        raise


# ============================================================
# 重试封装
# ============================================================

async def _retry_with_backoff(
    caller_func,
    model_name: str,
    system_prompt: str,
    user_message: str,
    images_base64: list[str],
    enable_web_search: bool,
) -> str:
    """多模态调用的带指数退避重试封装

    Args:
        caller_func: LLM 调用函数
        model_name: 模型名称（用于日志）
        其余参数透传给 caller_func

    Returns:
        LLM 响应文本

    Raises:
        RuntimeError: 所有重试均失败
    """
    last_error = None
    last_error_detail = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "[LLM] 调用 %s (第 %d/%d 次), images=%d, search=%s",
                model_name, attempt + 1, MAX_RETRIES,
                len(images_base64), enable_web_search,
            )
            result = await asyncio.wait_for(
                caller_func(
                    system_prompt,
                    user_message,
                    images_base64,
                    enable_web_search,
                ),
                timeout=TIMEOUT_SECONDS,
            )

            if result and result.strip():
                logger.info(
                    "[LLM] %s 调用成功, 响应长度=%d",
                    model_name, len(result),
                )
                return result

            # 空响应也视为失败
            raise ValueError(f"{model_name} 返回空响应")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"{model_name} 调用超时（{TIMEOUT_SECONDS}s）")
            last_error_detail = f"TIMEOUT: {model_name} 调用超时（{TIMEOUT_SECONDS}s）"
            logger.warning("[LLM] %s 超时 (attempt %d)", model_name, attempt + 1)
        except Exception as e:
            last_error = e
            last_error_detail = f"{type(e).__name__}: {str(e)}"
            logger.warning(
                "[LLM] %s 调用异常 (attempt %d): %s",
                model_name, attempt + 1, last_error_detail,
            )

        # 最后一次尝试不等待
        if attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY * (2 ** attempt)
            logger.info("[LLM] 等待 %.0fs 后重试...", delay)
            await asyncio.sleep(delay)

    logger.error("[LLM] %s 所有重试均失败: %s", model_name, last_error_detail)
    raise RuntimeError(
        f"{model_name} 调用失败（重试 {MAX_RETRIES} 次后）: {last_error_detail}"
    ) from last_error


async def _retry_with_backoff_text(
    caller_func,
    model_name: str,
    system_prompt: str,
    user_message: str,
) -> str:
    """纯文本调用的重试封装"""
    last_error = None
    last_error_detail = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "[LLM] 调用 %s 纯文本 (第 %d/%d 次)",
                model_name, attempt + 1, MAX_RETRIES,
            )
            result = await asyncio.wait_for(
                caller_func(system_prompt, user_message),
                timeout=TIMEOUT_SECONDS,
            )

            if result and result.strip():
                logger.info(
                    "[LLM] %s 纯文本调用成功, 响应长度=%d",
                    model_name, len(result),
                )
                return result

            raise ValueError(f"{model_name} 返回空响应")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"{model_name} 文档分析超时（{TIMEOUT_SECONDS}s）")
            last_error_detail = f"TIMEOUT: {model_name} 超时"
            logger.warning("[LLM] %s 超时 (attempt %d)", model_name, attempt + 1)
        except Exception as e:
            last_error = e
            last_error_detail = f"{type(e).__name__}: {str(e)}"
            logger.warning(
                "[LLM] %s 异常 (attempt %d): %s",
                model_name, attempt + 1, last_error_detail,
            )

        if attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY * (2 ** attempt)
            logger.info("[LLM] 等待 %.0fs 后重试...", delay)
            await asyncio.sleep(delay)

    logger.error("[LLM] %s 所有重试均失败: %s", model_name, last_error_detail)
    raise RuntimeError(
        f"{model_name} 调用失败（重试 {MAX_RETRIES} 次后）: {last_error_detail}"
    ) from last_error


# ============================================================
# 公有 API
# ============================================================

async def analyze_design(
    images_base64: list[str],
    extracted_texts: Optional[list[str]] = None,
    input_text: Optional[str] = None,
    enable_web_search: Optional[bool] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """调用多模态 LLM 分析设计图

    Args:
        images_base64: Base64 编码的图片列表
        extracted_texts: 上传文件提取的文本列表
        input_text: 用户补充文本
        enable_web_search: 是否启用联网搜索
        system_prompt: 完整的系统提示词（由 prompt_builder 构建）

    Returns:
        LLM 响应文本（期望为 JSON 格式）

    Raises:
        RuntimeError: 所有重试均失败
    """
    from .prompt_builder import build_system_prompt, build_user_message

    if enable_web_search is None:
        enable_web_search = settings.ENABLE_WEB_SEARCH

    # 构建系统提示词（如果未提供）
    if system_prompt is None:
        system_prompt = build_system_prompt(enable_web_search)

    # 构建用户消息
    user_message = build_user_message(extracted_texts, input_text)

    logger.info(
        "[LLM] analyze_design 开始: images=%d, extracted_texts=%d, input_text=%s, web_search=%s, system_prompt_len=%d, model=%s",
        len(images_base64),
        len(extracted_texts) if extracted_texts else 0,
        "有" if input_text else "无",
        enable_web_search,
        len(system_prompt),
        settings.LLM_MODEL_NAME,
    )

    return await _retry_with_backoff(
        _call_llm,
        settings.LLM_MODEL_NAME,
        system_prompt,
        user_message,
        images_base64,
        enable_web_search,
    )


async def analyze_document(
    document_text: str,
    filename: str = "",
) -> str:
    """调用 LLM 分析文档（合同/报价单审核）

    Args:
        document_text: 从 PDF/文件提取的文档纯文本
        filename: 原始文件名（用于日志）

    Returns:
        LLM 响应文本（期望为 JSON 格式的 risks 列表）

    Raises:
        RuntimeError: 所有重试均失败
    """
    from .prompt_builder import build_document_analysis_prompt

    system_prompt = build_document_analysis_prompt()

    user_message = f"""请审核以下装修相关的合同/报价文档，逐项检查本地知识库中的所有陷阱。

文档名称：{filename if filename else '未知文件'}

文档内容：
{document_text}

请严格按照 JSON 格式输出分析结果。"""

    logger.info(
        "[LLM] analyze_document 开始: file=%s, text_len=%d, system_prompt_len=%d, model=%s",
        filename, len(document_text), len(system_prompt), settings.LLM_MODEL_NAME,
    )

    return await _retry_with_backoff_text(
        _call_llm_text,
        settings.LLM_MODEL_NAME,
        system_prompt,
        user_message,
    )


async def predict_extra_items(
    document_analysis_json: dict,
) -> str:
    """基于报价单分析结果，预测增项与总花费估算

    Args:
        document_analysis_json: 报价单/合同分析的 risks_json 字典

    Returns:
        LLM 响应文本（期望为 JSON 格式的 extra_item_prediction）

    Raises:
        RuntimeError: 所有重试均失败
    """
    from .prompt_builder import build_extra_prediction_prompt

    # 将分析结果序列化为文本摘要
    import json as json_module
    analysis_summary_text = json_module.dumps(
        document_analysis_json,
        ensure_ascii=False,
        indent=2,
    )

    system_prompt = build_extra_prediction_prompt(analysis_summary_text)

    user_message = """请基于以上报价单分析结果和增项套路知识库，预测装修公司最可能追加的增项项目和金额。

请严格按照 JSON 格式输出预测结果。"""

    logger.info(
        "[LLM] predict_extra_items 开始: analysis_summary_len=%d, system_prompt_len=%d, model=%s",
        len(analysis_summary_text), len(system_prompt), settings.LLM_MODEL_NAME,
    )

    return await _retry_with_backoff_text(
        _call_llm_text,
        settings.LLM_MODEL_NAME,
        system_prompt,
        user_message,
    )


async def extract_document_summary(
    document_text: str,
    filename: str,
    doc_type: str = "general",
) -> str:
    """调用 LLM 提取单份文档的结构化摘要

    Args:
        document_text: 文档纯文本
        filename: 文件名
        doc_type: 文档类型（quotation / contract / supervision_report / general）

    Returns:
        LLM 响应文本（期望为 JSON 格式的结构化摘要）
    """
    from .document_extractor import build_extraction_system_prompt, build_extraction_user_message

    system_prompt = build_extraction_system_prompt(doc_type)
    user_message = build_extraction_user_message(document_text, filename)

    logger.info(
        "[LLM] extract_document_summary 开始: file=%s, doc_type=%s, text_len=%d, model=%s",
        filename, doc_type, len(document_text), settings.LLM_MODEL_NAME,
    )

    return await _retry_with_backoff_text(
        _call_llm_text,
        settings.LLM_MODEL_NAME,
        system_prompt,
        user_message,
    )


async def cross_check_documents(
    check_mode: str,
    doc_summaries: list[dict],
) -> str:
    """调用 LLM 进行多文档交叉比对

    Args:
        check_mode: 比对模式
        doc_summaries: 文档结构化摘要列表

    Returns:
        LLM 响应文本（期望为 JSON 格式的交叉核查结果）
    """
    from .prompt_builder import build_cross_check_prompt

    enable_supervision_tracking = (check_mode == "SUPERVISION_TRACKING")
    system_prompt, user_message = build_cross_check_prompt(
        check_mode=check_mode,
        doc_summaries=doc_summaries,
        enable_supervision_tracking=enable_supervision_tracking,
    )

    logger.info(
        "[LLM] cross_check_documents 开始: check_mode=%s, doc_count=%d, model=%s",
        check_mode, len(doc_summaries), settings.LLM_MODEL_NAME,
    )

    return await _retry_with_backoff_text(
        _call_llm_text,
        settings.LLM_MODEL_NAME,
        system_prompt,
        user_message,
    )