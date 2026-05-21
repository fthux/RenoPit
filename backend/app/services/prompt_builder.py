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


def load_pitfalls() -> dict:
    """便捷函数：加载完整 pitfalls.json 数据

    Returns:
        完整的 pitfalls JSON 字典
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PitfallsLoader()
    return _default_loader.load()