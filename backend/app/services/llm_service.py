"""
LLM Service — 多模态大模型调用服务
支持 OpenAI (GPT-4o) 和 Gemini，模型回退，联网搜索，重试机制
"""

import asyncio
import base64
import logging
import time
from typing import Optional

from openai import AsyncOpenAI
import google.generativeai as genai

from ..core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# 常量
# ============================================================

# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 秒，指数退避：2s → 4s → 8s
TIMEOUT_SECONDS = 120

# 模型名称
OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-2.5-flash"


# ============================================================
# OpenAI 客户端（延迟初始化）
# ============================================================

_openai_client: Optional[AsyncOpenAI] = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=TIMEOUT_SECONDS,
        )
    return _openai_client


# ============================================================
# Gemini 客户端（延迟配置）
# ============================================================

_gemini_configured: bool = False


def _configure_gemini() -> None:
    """延迟配置 Gemini API key"""
    global _gemini_configured
    if not _gemini_configured and settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_configured = True


# ============================================================
# 工具定义
# ============================================================

# OpenAI web_search 工具定义
WEB_SEARCH_TOOL_OPENAI = {
    "type": "web_search_preview",
    "search_context_size": "medium",
}


# ============================================================
# OpenAI 调用
# ============================================================

async def _call_openai(
    system_prompt: str,
    user_message: str,
    images_base64: list[str],
    enable_web_search: bool,
) -> str:
    """调用 OpenAI GPT-4o 多模态 API

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
        "[OpenAI] 开始构建请求: images=%d, user_message_len=%d, system_prompt_len=%d, web_search=%s",
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
            "[OpenAI] 图片 %d/%d: mime=%s, base64_len=%d",
            i + 1, len(images_base64), mime_type, len(img_data),
        )

    # 添加文本
    content_parts.append({
        "type": "text",
        "text": user_message if user_message else "请分析以上设计图",
    })

    # 构建请求参数
    tools: Optional[list] = None
    if enable_web_search:
        tools = [WEB_SEARCH_TOOL_OPENAI]
        logger.info("[OpenAI] 已启用联网搜索工具")

    logger.info("[OpenAI] 正在发送请求到 API...")

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_parts},
            ],
            tools=tools,
            max_tokens=4096,
            temperature=0.3,  # 低温度提高一致性
        )

        result = response.choices[0].message.content or ""
        logger.info(
            "[OpenAI] API 调用成功: response_len=%d, finish_reason=%s",
            len(result),
            response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else 'unknown',
        )

        # 记录是否有工具调用（联网搜索）
        if response.choices[0].message.tool_calls:
            logger.info(
                "[OpenAI] 模型使用了工具调用: %d 个工具",
                len(response.choices[0].message.tool_calls),
            )

        return result
    except Exception as e:
        logger.error(
            "[OpenAI] API 调用异常: %s (type=%s)",
            str(e), type(e).__name__,
        )
        raise


# ============================================================
# Gemini 调用
# ============================================================

async def _call_gemini(
    system_prompt: str,
    user_message: str,
    images_base64: list[str],
    enable_web_search: bool,
) -> str:
    """调用 Gemini 多模态 API

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
    _configure_gemini()

    logger.info(
        "[Gemini] 开始构建请求: images=%d, user_message_len=%d, system_prompt_len=%d, web_search=%s",
        len(images_base64), len(user_message or ""), len(system_prompt or ""), enable_web_search,
    )

    # 构建内容 parts
    parts: list = []

    # 构建文本部分
    text_content = (
        f"{user_message}\n\n请输出 JSON 格式的分析结果。"
        if user_message
        else "请输出 JSON 格式的分析结果。"
    )
    parts.append({"text": text_content})

    # 添加图片（Gemini SDK 格式要求先文本后图片，内联数据）
    for i, img_b64 in enumerate(images_base64):
        # 清理 data URL 前缀
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

        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": img_data,
            }
        })
        logger.info(
            "[Gemini] 图片 %d/%d: mime=%s, base64_len=%d",
            i + 1, len(images_base64), mime_type, len(img_data),
        )

    # 构建生成配置
    generation_config = genai.GenerationConfig(
        max_output_tokens=100000,
        temperature=0.3,
    )

    # 调用 Gemini（同步方式，在 asyncio executor 中运行）
    loop = asyncio.get_event_loop()
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=system_prompt if system_prompt else None,
    )

    generate_kwargs: dict = {}
    if enable_web_search:
        # google-generativeai 0.8.0 不支持 google_search_retrieval 工具
        # 在 SDK 0.8.0 中联网搜索只能通过 API 默认行为触发
        # 高版本 SDK 可以传入 tools=[genai.protos.Tool(google_search_retrieval=genai.protos.GoogleSearchRetrieval())]
        logger.warning("[Gemini] SDK 0.8.0 不支持联网搜索工具参数，静默跳过")

    logger.info("[Gemini] 正在发送请求到 API...")

    try:
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                parts,
                generation_config=generation_config,
                **generate_kwargs,
            ),
        )

        logger.info(
            "[Gemini] API 调用成功测试: response=%d",
            response,
        )
        result = response.text or ""
        logger.info(
            "[Gemini] API 调用成功: response_len=%d",
            len(result),
        )
        return result

    except Exception as e:
        logger.error(
            "[Gemini] API 调用异常: %s (type=%s)",
            str(e), type(e).__name__,
        )
        raise


# ============================================================
# 主调用函数
# ============================================================

async def analyze_design(
    images_base64: list[str],
    extracted_texts: Optional[list[str]] = None,
    input_text: Optional[str] = None,
    enable_web_search: Optional[bool] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """调用多模态 LLM 分析设计图

    自动选择主模型和备用模型，支持重试和超时。

    Args:
        images_base64: Base64 编码的图片列表
        extracted_texts: 上传文件提取的文本列表
        input_text: 用户补充文本
        enable_web_search: 是否启用联网搜索
        system_prompt: 完整的系统提示词（由 prompt_builder 构建）

    Returns:
        LLM 响应文本（期望为 JSON 格式）

    Raises:
        RuntimeError: 所有模型调用均失败
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
        "[LLM] analyze_design 开始: images=%d, extracted_texts=%d, input_text=%s, web_search=%s, system_prompt_len=%d",
        len(images_base64),
        len(extracted_texts) if extracted_texts else 0,
        "有" if input_text else "无",
        enable_web_search,
        len(system_prompt),
    )

    # 确定主要和备用模型
    provider = settings.AI_MODEL_PROVIDER.lower()
    logger.info("[LLM] 当前配置: AI_MODEL_PROVIDER=%s, OPENAI_API_KEY=%s, GEMINI_API_KEY=%s",
        provider,
        "已配置 (前8位: %s)" % settings.OPENAI_API_KEY[:8] if settings.OPENAI_API_KEY else "未配置",
        "已配置" if settings.GEMINI_API_KEY else "未配置",
    )

    if provider == "gemini":
        primary_caller = _call_gemini
        primary_name = "Gemini"
        fallback_caller = _call_openai
        fallback_name = "OpenAI GPT-4o"
    else:
        primary_caller = _call_openai
        primary_name = "OpenAI GPT-4o"
        fallback_caller = _call_gemini
        fallback_name = "Gemini"

    last_error = None

    # 尝试主模型（含重试）
    try:
        logger.info("[LLM] 尝试主模型: %s", primary_name)
        return await _retry_with_backoff(
            primary_caller,
            primary_name,
            system_prompt,
            user_message,
            images_base64,
            enable_web_search,
        )
    except Exception as e:
        last_error = e
        logger.error("[LLM] 主模型 %s 失败: %s", primary_name, str(e))
        # 主模型失败，尝试备用模型
        try:
            logger.info("[LLM] 尝试备用模型: %s", fallback_name)
            return await _retry_with_backoff(
                fallback_caller,
                fallback_name,
                system_prompt,
                user_message,
                images_base64,
                enable_web_search,
            )
        except Exception as fallback_error:
            full_error = (
                f"所有模型调用均失败。主模型({primary_name}): {last_error}，"
                f"备用模型({fallback_name}): {fallback_error}"
            )
            logger.error("[LLM] %s", full_error)
            raise RuntimeError(full_error) from fallback_error


async def analyze_document(
    document_text: str,
    filename: str = "",
) -> str:
    """调用纯文本文档分析（合同/报价单审核），不使用多模态图片

    使用主模型进行仅文本分析，审核合同条款和报价陷阱。

    Args:
        document_text: 从 PDF/文件提取的文档纯文本
        filename: 原始文件名（用于日志）

    Returns:
        LLM 响应文本（期望为 JSON 格式的 risks 列表）

    Raises:
        RuntimeError: 所有模型调用均失败
    """
    from .prompt_builder import build_document_analysis_prompt

    system_prompt = build_document_analysis_prompt()

    user_message = f"""请审核以下装修相关的合同/报价文档，逐项检查本地知识库中的所有陷阱。

文档名称：{filename if filename else '未知文件'}

文档内容：
{document_text}

请严格按照 JSON 格式输出分析结果。"""

    logger.info(
        "[LLM] analyze_document 开始: file=%s, text_len=%d, system_prompt_len=%d",
        filename, len(document_text), len(system_prompt),
    )

    provider = settings.AI_MODEL_PROVIDER.lower()
    last_error = None

    # 确定主模型和备用模型（文本仅用 OpenAI 格式也可以，Gemini 也支持纯文本）
    if provider == "gemini":
        primary_caller = _call_gemini_text
        primary_name = "Gemini"
        fallback_caller = _call_openai_text
        fallback_name = "OpenAI GPT-4o"
    else:
        primary_caller = _call_openai_text
        primary_name = "OpenAI GPT-4o"
        fallback_caller = _call_gemini_text
        fallback_name = "Gemini"

    # 尝试主模型
    try:
        logger.info("[LLM] 文档分析尝试主模型: %s", primary_name)
        return await _retry_with_backoff_text(
            primary_caller,
            primary_name,
            system_prompt,
            user_message,
        )
    except Exception as e:
        last_error = e
        logger.error("[LLM] 文档分析主模型 %s 失败: %s", primary_name, str(e))
        try:
            logger.info("[LLM] 文档分析尝试备用模型: %s", fallback_name)
            return await _retry_with_backoff_text(
                fallback_caller,
                fallback_name,
                system_prompt,
                user_message,
            )
        except Exception as fallback_error:
            full_error = (
                f"文档分析所有模型调用均失败。主模型({primary_name}): {last_error}，"
                f"备用模型({fallback_name}): {fallback_error}"
            )
            logger.error("[LLM] %s", full_error)
            raise RuntimeError(full_error) from fallback_error


async def predict_extra_items(
    document_analysis_json: dict,
) -> str:
    """基于报价单分析结果，预测增项与总花费估算

    调用 LLM 分析报价单中已识别的风险项（漏项、模糊计价等），
    预测装修公司后期可能追加的项目和费用。

    Args:
        document_analysis_json: 报价单/合同分析的 risks_json 字典

    Returns:
        LLM 响应文本（期望为 JSON 格式的 extra_item_prediction）

    Raises:
        RuntimeError: 所有模型调用均失败
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
        "[LLM] predict_extra_items 开始: analysis_summary_len=%d, system_prompt_len=%d",
        len(analysis_summary_text), len(system_prompt),
    )

    provider = settings.AI_MODEL_PROVIDER.lower()
    last_error = None

    if provider == "gemini":
        primary_caller = _call_gemini_text
        primary_name = "Gemini"
        fallback_caller = _call_openai_text
        fallback_name = "OpenAI GPT-4o"
    else:
        primary_caller = _call_openai_text
        primary_name = "OpenAI GPT-4o"
        fallback_caller = _call_gemini_text
        fallback_name = "Gemini"

    try:
        logger.info("[LLM] 增项预测尝试主模型: %s", primary_name)
        return await _retry_with_backoff_text(
            primary_caller,
            primary_name,
            system_prompt,
            user_message,
        )
    except Exception as e:
        last_error = e
        logger.error("[LLM] 增项预测主模型 %s 失败: %s", primary_name, str(e))
        try:
            logger.info("[LLM] 增项预测尝试备用模型: %s", fallback_name)
            return await _retry_with_backoff_text(
                fallback_caller,
                fallback_name,
                system_prompt,
                user_message,
            )
        except Exception as fallback_error:
            full_error = (
                f"增项预测所有模型调用均失败。主模型({primary_name}): {last_error}，"
                f"备用模型({fallback_name}): {fallback_error}"
            )
            logger.error("[LLM] %s", full_error)
            raise RuntimeError(full_error) from fallback_error


async def _call_openai_text(
    system_prompt: str,
    user_message: str,
) -> str:
    """调用 OpenAI GPT-4o 纯文本分析"""
    client = _get_openai_client()
    logger.info("[OpenAI-Text] 开始请求, user_message_len=%d", len(user_message))

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=4096,
            temperature=0.3,
        )
        result = response.choices[0].message.content or ""
        logger.info("[OpenAI-Text] 调用成功: response_len=%d", len(result))
        return result
    except Exception as e:
        logger.error("[OpenAI-Text] 调用异常: %s", str(e))
        raise


async def _call_gemini_text(
    system_prompt: str,
    user_message: str,
) -> str:
    """调用 Gemini 纯文本分析"""
    _configure_gemini()
    loop = asyncio.get_event_loop()

    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=system_prompt if system_prompt else None,
    )

    generation_config = genai.GenerationConfig(
        max_output_tokens=100000,
        temperature=0.3,
    )

    logger.info("[Gemini-Text] 开始请求, user_message_len=%d", len(user_message))

    try:
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(user_message, generation_config=generation_config),
        )
        result = response.text or ""
        logger.info("[Gemini-Text] 调用成功: response_len=%d", len(result))
        return result
    except Exception as e:
        logger.error("[Gemini-Text] 调用异常: %s", str(e))
        raise


async def _retry_with_backoff_text(
    caller_func,
    model_name: str,
    system_prompt: str,
    user_message: str,
) -> str:
    """文档分析专用的重试封装"""
    last_error = None
    last_error_detail = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "[LLM] 调用 %s 文档分析 (第 %d/%d 次)",
                model_name, attempt + 1, MAX_RETRIES,
            )
            result = await asyncio.wait_for(
                caller_func(system_prompt, user_message),
                timeout=TIMEOUT_SECONDS,
            )

            if result and result.strip():
                logger.info(
                    "[LLM] %s 文档分析成功, 响应长度=%d",
                    model_name, len(result),
                )
                return result

            raise ValueError(f"{model_name} 返回空响应")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"{model_name} 文档分析超时（{TIMEOUT_SECONDS}s）")
            last_error_detail = f"TIMEOUT: {model_name} 超时"
            logger.warning("[LLM] %s 文档分析超时 (attempt %d)", model_name, attempt + 1)
        except Exception as e:
            last_error = e
            last_error_detail = f"{type(e).__name__}: {str(e)}"
            logger.warning(
                "[LLM] %s 文档分析异常 (attempt %d): %s",
                model_name, attempt + 1, last_error_detail,
            )

        if attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY * (2 ** attempt)
            logger.info("[LLM] 等待 %.0fs 后重试...", delay)
            await asyncio.sleep(delay)

    logger.error("[LLM] %s 文档分析所有重试均失败: %s", model_name, last_error_detail)
    raise RuntimeError(
        f"{model_name} 文档分析失败（重试 {MAX_RETRIES} 次后）: {last_error_detail}"
    ) from last_error


async def _retry_with_backoff(
    caller_func,
    model_name: str,
    system_prompt: str,
    user_message: str,
    images_base64: list[str],
    enable_web_search: bool,
) -> str:
    """带指数退避的重试封装

    Args:
        caller_func: 调用函数（_call_openai 或 _call_gemini）
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
