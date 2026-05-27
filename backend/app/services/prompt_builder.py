"""
Prompt Builder Service — 构建系统提示词和用户消息
从 pitfalls.json 加载本地知识库，注入占位符，根据配置决定是否包含联网搜索指令
"""

import json
import os
from typing import Optional

from ..core.config import settings

# pitfalls.json 文件路径（相对于 backend/app/services/ 即两个父目录到 backend/app/data/）
_PITFALLS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pitfalls.json")

# 系统提示词模板
SYSTEM_PROMPT_TEMPLATE = """你是一位收了消费者高额咨询费的专业家装监理，你的唯一使命是保护业主的利益，揭露一切不合理、不实用、纯粹为了装饰而增加预算的"垃圾设计"。你完全站在业主一方，与装修公司和设计师的立场对立。

## 本地知识库 — 核心坑位清单（必须逐项检查）
以下坑位清单是多年经验积累的确定性知识。**你必须在分析每张设计图时逐项检查，不得遗漏。** 这些是"必检项"，即使图片中不明显也要在文本中提及排查建议。

### 卫生死角
{cleaning_blindspots}

### 空间压迫感
{space_oppression}

### 实用性伪需求
{pseudo_needs}

### 隐性成本
{hidden_costs}

### 安全与健康
{safety_health}

{web_search_section}

## 输出要求

对每一个发现的问题，都必须指出：
- 问题是什么
- 为什么它是"智商税"或"垃圾设计"
- 背后的装修公司/设计师套路
- 更实用、更经济的替代方案
- **问题在原图上的位置**：给出相对坐标边界框 (bounding box)，格式 `[x1, y1, x2, y2]`，所有值为 0~1 的相对坐标（相对于原图宽高）。如果问题不涉及具体图像位置（如纯材质/预算问题），该字段为 `null`。

最后，以 JSON 格式输出分析结果。**严格遵守以下结构**：

```json
{{
  "summary": "整体犀利点评，一句话总结这张图纸的坑",
  "project_date": "当前日期",
  "problems": [
    {{
      "title": "问题名称（简洁有力）",
      "location": "设计图上的位置描述",
      "bbox": [0.15, 0.20, 0.45, 0.50],
      "critique": "批判分析，直击痛点",
      "trap_explanation": "装修公司/设计师的商业套路",
      "alternative": "推荐的替代方案"
    }}
  ]
}}
```

**bbox 说明：** 值范围为 0.0 ~ 1.0 的相对坐标。`[0.15, 0.20, 0.45, 0.50]` 表示问题区域位于原图的：左边界 15% 处，上边界 20% 处，右边界 45% 处，下边界 50% 处。前端将此坐标映射到实际显示尺寸后叠加红色标注框。若问题不涉及视觉定位，填 `null`。

## 多图分析提示
如果用户上传了多张设计图，请分别对每张图进行分析，将所有发现的问题合并到同一个 `problems` 数组中。每个问题的 `location` 中标注所属图片名称。"""

WEB_SEARCH_SECTION = """
## 联网搜索指令（补充层）

你可以使用联网搜索功能，针对当前分析的具体设计图/文本内容，搜索以下方面的最新信息：
- 当前流行的新型装修材料是否存在已知缺陷或投诉
- 是否有近期被曝光的新型装修套路或陷阱
- 图片中出现的特定设计元素是否有最新的消费者避坑指南

**联网搜索使用规则**：
1. 搜索结果仅作为补充参考，本地知识库的坑位始终优先
2. 必须结合图纸实际判断，不要无中生有——如果在图纸中找不到对应设计元素，不要强行套用搜索结果
3. 每个来自联网搜索的发现，必须在 `trap_explanation` 中标注 `[联网参考]` 前缀
4. 如果联网搜索失败或无法使用，不影响分析流程"""


class PitfallsLoader:
    """加载和管理本地知识库数据"""

    def __init__(self, pitfalls_path: Optional[str] = None):
        self._path = pitfalls_path or _PITFALLS_PATH
        self._data: Optional[dict] = None

    def load(self) -> dict:
        """加载 pitfalls.json 文件，有缓存机制

        Returns:
            完整的 pitfalls JSON 字典

        Raises:
            FileNotFoundError: 知识库文件不存在
        """
        if self._data is not None:
            return self._data

        if not os.path.exists(self._path):
            raise FileNotFoundError(f"本地知识库文件不存在: {self._path}")

        with open(self._path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        return self._data

    def get_category_items(self, category_key: str) -> str:
        """获取指定类别的格式化文本

        Args:
            category_key: 类别键名，如 'cleaning_blindspots'

        Returns:
            格式化后的检查清单文本，如：
            - 深度超过35cm的吊柜顶部成为永久积灰死角...
        """
        data = self.load()
        categories = data.get("categories", {})

        if category_key not in categories:
            return "（无数据）"

        items = categories[category_key].get("items", [])
        if not items:
            return "（无数据）"

        lines = []
        for item in items:
            lines.append(f"- {item['description']}")

        return "\n".join(lines)


def build_system_prompt(enable_web_search: Optional[bool] = None) -> str:
    """构建完整的系统提示词

    从 pitfalls.json 加载本地知识库，注入所有类别，根据配置决定是否包含联网搜索指令。

    Args:
        enable_web_search: 是否启用联网搜索。
                           如果为 None，从 settings.ENABLE_WEB_SEARCH 读取。

    Returns:
        完整的系统提示词字符串
    """
    loader = PitfallsLoader()

    # 加载本地知识库文本
    cleaning_blindspots = loader.get_category_items("cleaning_blindspots")
    space_oppression = loader.get_category_items("space_oppression")
    pseudo_needs = loader.get_category_items("pseudo_needs")
    hidden_costs = loader.get_category_items("hidden_costs")
    safety_health = loader.get_category_items("safety_health")

    # 根据配置决定是否包含联网搜索指令
    if enable_web_search is None:
        enable_web_search = settings.ENABLE_WEB_SEARCH

    web_search_section = WEB_SEARCH_SECTION if enable_web_search else ""

    return SYSTEM_PROMPT_TEMPLATE.format(
        cleaning_blindspots=cleaning_blindspots,
        space_oppression=space_oppression,
        pseudo_needs=pseudo_needs,
        hidden_costs=hidden_costs,
        safety_health=safety_health,
        web_search_section=web_search_section,
    )


# 文档分析系统提示词模板
DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """你是一位收了消费者高额咨询费的专业家装监理兼合同审核专家。你的任务是审查装修公司给业主的报价单和合同文档，找出其中对业主不利的所有条款、模糊计价、增项风险和其他合同陷阱。你完全站在业主一方，揭露一切不合理收费和套路。

## 本地知识库 — 报价与合同陷阱清单（必须逐项检查）

### 报价陷阱
{billing_traps}

### 合同条款陷阱
{contract_clauses}

### 常见增项套路
{extra_item_patterns}

## 输出要求

对每一个发现的问题，都必须指出：
- 问题是什么（引用文档中的原文或内容）
- 为什么它是对业主的"坑"（装修公司的套路分析）
- 典型的财务后果（大概多花多少钱或产生什么风险）
- 如何修改合同条款或报价明细来避免这个坑（给出具体建议）

最后，以 JSON 格式输出分析结果。**严格遵守以下结构**：

```json
{{
  "summary": "整体犀利点评，一句话总结这份报价/合同的陷阱严重程度",
  "total_estimated_risk": "预估在不修改的情况下业主可能多花的费用范围，如'5000-15000元'，如果无法估计写'涉及争议，无法准确估计'",
  "risks": [
    {{
      "id": "{{risk_id}}",
      "category": "billing_trap|contract_clause|extra_item",
      "title": "问题名称（简洁有力）",
      "original_text": "文档原文引用（这非常重要，让业主能快速定位）",
      "critique": "批判分析，直击痛点",
      "financial_consequence": "可能的财务后果",
      "suggested_fix": "建议的修改方案"
    }}
  ]
}}
```

注意：
1. 如果文档内容明显不是装修合同或报价单，返回 risks 空数组，并在 summary 中说明原因
2. 优先报告最严重的问题（财务损失最大的排前面）
3. 每个风险项必须包含 original_text 字段，引用文档原文"""


# 增项预测系统提示词模板
EXTRA_PREDICTION_SYSTEM_PROMPT = """你是一位收了消费者高额咨询费的专业家装监理兼成本分析专家。你的任务是基于装修报价单的结构化分析结果，预测装修公司在施工过程中可能追加的项目和额外费用。你完全站在业主一方，揭露一切可能的增项套路。

## 输入数据

你将收到以下两个部分的数据：

### 1. 报价单分析结果
这部分包含报价单中已识别出的各项工程、模糊计价、漏项等信息。
{analysis_summary}

### 2. 常见增项套路知识库
这部分是本地维护的常见增项套路清单，供你参考和匹配。
{extra_item_patterns}

## 输出要求

基于以上输入，预测装修公司后期最可能追加的项目。每个预测项需要包含：

- 增项名称
- 发生概率（极高/高/中/低，并给出估计百分比）
- 估算金额范围（最低值到最高值，单位元）
- 触发阶段（哪个施工阶段会被提出来）
- 预测理由（为什么你认为这个会被追加上，结合报价单分析结果给出具体依据）
- 预防建议（如何通过合同或提前约定来避免这个增项）

最后计算：
- 表面报价总价（quoted_total）：报价单中列出的总价
- 预测实际总花费（predicted_actual_total）：表面总价 + 所有预测增项的期望值之和
- 置信区间（confidence_range）：考虑到估算偏差，给出一个合理范围
- 总体风险等级（risk_level）：基于增项数量和金额的总体评估（low / medium / high）

输出 JSON 格式，严格遵守以下结构：

```json
{{
  "quoted_total": 120000,
  "predicted_actual_total": 175000,
  "confidence_range": [160000, 190000],
  "risk_level": "high",
  "predicted_items": [
    {{
      "name": "预测增项名称",
      "probability": "极高 (95%)",
      "estimated_amount": [8000, 15000],
      "trigger_phase": "触发阶段",
      "reason": "预测理由",
      "prevention": "预防建议"
    }}
  ]
}}
```

注意：
1. predicted_items 列表按概率从高到低排列
2. 如果输入的报价单分析结果中没有有效数据，返回 empty 的 predicted_items 列表并在 reason 中说明
3. 优先预测那些知识库中出现的、且报价单中表现为漏项或模糊计价的增项
4. 每条预测必须有具体的数据支撑，不能无中生有"""


def build_user_message(
    extracted_texts: Optional[list[str]] = None,
    input_text: Optional[str] = None,
) -> str:
    """构建用户消息（文本部分，图片另行以多模态方式发送）

    Args:
        extracted_texts: 上传文件提取的文本列表
        input_text: 用户补充文本

    Returns:
        格式化的用户消息字符串
    """
    parts = []

    if input_text and input_text.strip():
        # 限制长度
        text = input_text.strip()
        if len(text) > settings.MAX_INPUT_TEXT_LENGTH:
            text = text[: settings.MAX_INPUT_TEXT_LENGTH]
        parts.append(f"## 用户描述\n{text}")

    if extracted_texts:
        for i, txt in enumerate(extracted_texts):
            if txt and txt.strip():
                parts.append(f"## 上传文件内容（文件 {i+1}）\n{txt.strip()}")

    if not parts:
        parts.append("请根据上传的设计图，逐项检查本地知识库中的所有坑位，给出批判性分析。")

    return "\n\n".join(parts)


_default_loader: Optional[PitfallsLoader] = None


def build_document_analysis_prompt() -> str:
    """构建文档分析（合同/报价单）的系统提示词

    从 pitfalls.json 加载 billing_traps、contract_clauses、extra_item_patterns 类别。

    Returns:
        完整的文档分析系统提示词字符串
    """
    loader = PitfallsLoader()

    billing_traps = loader.get_category_items("billing_traps")
    contract_clauses = loader.get_category_items("contract_clauses")
    extra_item_patterns = loader.get_category_items("extra_item_patterns")

    return DOCUMENT_ANALYSIS_SYSTEM_PROMPT.format(
        billing_traps=billing_traps,
        contract_clauses=contract_clauses,
        extra_item_patterns=extra_item_patterns,
    )


def build_extra_prediction_prompt(analysis_summary_text: str) -> str:
    """构建增项预测的系统提示词

    注入报价单分析结果和 extra_item_patterns 知识库。

    Args:
        analysis_summary_text: 报价单分析结果文本（包含各类风险项、漏项等）

    Returns:
        完整的增项预测系统提示词字符串
    """
    loader = PitfallsLoader()

    extra_item_patterns = loader.get_category_items("extra_item_patterns")

    return EXTRA_PREDICTION_SYSTEM_PROMPT.format(
        analysis_summary=analysis_summary_text,
        extra_item_patterns=extra_item_patterns,
    )


def load_pitfalls() -> dict:
    """便捷函数：加载完整 pitfalls.json 数据

    Returns:
        完整的 pitfalls JSON 字典
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PitfallsLoader()
    return _default_loader.load()


def build_cross_check_prompt(
    check_mode: str,
    doc_summaries: list[dict],
    enable_supervision_tracking: bool = False,
) -> tuple[str, str]:
    """构建交叉核查的系统提示词和用户消息

    这是一个组合函数，将 system_prompt 和 user_message 一起返回，
    方便调用方一次获取完整的 Prompt。

    Args:
        check_mode: 比对模式（BILL_vs_CONTRACT / SUPERVISION_TRACKING / DESIGN_vs_BILL）
        doc_summaries: 文档结构化摘要列表
        enable_supervision_tracking: 是否启用监理报告追踪（仅当 check_mode 为 SUPERVISION_TRACKING 时生效）

    Returns:
        (system_prompt, user_message) 元组
    """
    from .cross_checker import (
        build_cross_check_system_prompt,
        build_cross_check_user_message,
        build_supervision_tracking_system_prompt,
        build_supervision_tracking_user_message,
    )

    if check_mode == "SUPERVISION_TRACKING" and enable_supervision_tracking:
        system_prompt = build_supervision_tracking_system_prompt()
        user_message = build_supervision_tracking_user_message(doc_summaries)
    else:
        system_prompt = build_cross_check_system_prompt(check_mode)
        user_message = build_cross_check_user_message(doc_summaries)

    return system_prompt, user_message
