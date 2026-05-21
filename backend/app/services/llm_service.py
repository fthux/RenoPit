"""
LLM Service — 多模态大模型调用服务
支持 OpenAI (GPT-4o) 和 Gemini，模型回退，联网搜索，重试机制
"""

import asyncio
import base64
import time
from typing import Optional

from openai import AsyncOpenAI
import google.generativeai as genai

from ..core.config import settings


# ============================================================
# 常量
# ============================================================

# 重试配置
MAX_RETRIES = 3
BASE_DELAY = 2  # 秒，指数退避：2s → 4s → 8s
TIMEOUT_SECONDS = 120

# 模型名称
OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"


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
    """
    client = _get_openai_client()

    # 构建消息内容
    content_parts = []

    # 添加图片
    for img_b64 in images_base64:
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

    # 添加文本
    content_parts.append({
        "type": "text",
        "text": user_message if user_message else "请分析以上设计图",
    })

    # 构建请求参数
    tools: Optional[list] = None
    if enable_web_search:
        tools = [WEB_SEARCH_TOOL_OPENAI]

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

    return response.choices[0].message.content or ""


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
    """
    _configure_gemini()

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
    for img_b64 in images_base64:
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

    # 构建生成配置
    generation_config = genai.GenerationConfig(
        max_output_tokens=4096,
        temperature=0.3,
    )

    model_kwargs: dict = {
        "model": GEMINI_MODEL,
        "contents": parts,
        "generation_config": generation_config,
    }

    # 系统提示词（Gemini SDK 支持 system_instruction 参数）
    if system_prompt:
        model_kwargs["system_instruction"] = system_prompt

    # 如果启用联网搜索，添加工具
    if enable_web_search:
        model_kwargs["tools"] = [{"google_search": {}}]

    # 调用 Gemini（同步方式，在 asyncio executor 中运行）
    loop = asyncio.get_event_loop()
    model = genai.GenerativeModel(GEMINI_MODEL)

    response = await loop.run_in_executor(
        None,
        lambda: model.generate_content(
            parts,
            generation_config=generation_config,
        ),
    )

    return response.text or ""


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

    # 确定主要和备用模型
    provider = settings.AI_MODEL_PROVIDER.lower()

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
        # 主模型失败，尝试备用模型
        try:
            return await _retry_with_backoff(
                fallback_caller,
                fallback_name,
                system_prompt,
                user_message,
                images_base64,
                enable_web_search,
            )
        except Exception as fallback_error:
            raise RuntimeError(
                f"所有模型调用均失败。主模型({primary_name}): {last_error}，"
                f"备用模型({fallback_name}): {fallback_error}"
            ) from fallback_error


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

    for attempt in range(MAX_RETRIES):
        try:
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
                return result

            # 空响应也视为失败
            raise ValueError(f"{model_name} 返回空响应")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"{model_name} 调用超时（{TIMEOUT_SECONDS}s）")
        except Exception as e:
            last_error = e

        # 最后一次尝试不等待
        if attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY * (2 ** attempt)
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"{model_name} 调用失败（重试 {MAX_RETRIES} 次后）: {last_error}"
    ) from last_error