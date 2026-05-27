"""
Document Extractor — 单文档结构化提取器
对单份文档用轻量 Prompt 提取浓缩的结构化摘要，大幅压缩 token 量。
不同 doc_type 使用不同的提取策略。
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 文档结构化提取的系统提示词模板
EXTRACTION_SYSTEM_PROMPT = """你是一位专业的装修文档分析助手。你的任务是从一份装修相关文档中提取关键信息，生成结构化的摘要。

## 当前文档类型：{doc_type}

请根据文档类型提取以下信息：

### 提取要求
1. 只提取文档中**明确存在**的信息，不要编造
2. 保持客观，不要添加主观评价
3. 严格控制摘要长度，每个字段尽量简洁
4. 如果某个字段在文档中不存在，输出 null 或空列表

### 输出格式
严格按照以下 JSON 结构输出：
{output_schema}
"""

# ============================================================
# 不同文档类型的输出 Schema
# ============================================================

BILL_SCHEMA = """{
  "doc_type": "quotation",
  "source_file": "文件名",
  "total_quoted": 120000.00,
  "currency": "CNY",
  "line_items_summary": [
    {
      "name": "项目名称",
      "unit_price": 85.00,
      "quantity": 35,
      "total_price": 2975.00,
      "material_brand": "材料品牌（如未知则null）",
      "notes": "备注（如"含水泥砂浆，不含瓷砖主材"等）"
    }
  ],
  "vague_pricing": [
    {
      "phrase": "按实结算",
      "context": "原文上下文片段",
      "items_involved": ["涉及的项目名称列表"]
    }
  ],
  "missing_items_checklist": {
    "水电改造": true,
    "墙面找平": false,
    "地面找平": false,
    "垃圾清运": true,
    "材料搬运": false,
    "美缝": false,
    "保洁": false
  },
  "key_terms_conditions": "付款方式、工期等关键条款摘要"
}"""

CONTRACT_SCHEMA = """{
  "doc_type": "contract",
  "source_file": "文件名",
  "contract_info": {
    "project_name": "工程名称",
    "contract_amount": 120000.00,
    "contract_date": "签约日期",
    "parties": "甲乙双方名称"
  },
  "scope_of_work": [
    "施工范围1：简要描述",
    "施工范围2：简要描述"
  ],
  "payment_schedule": {
    "installment_1": {"ratio": "30%", "trigger": "开工前", "amount": 36000},
    "installment_2": {"ratio": "40%", "trigger": "水电验收后", "amount": 48000},
    "installment_3": {"ratio": "25%", "trigger": "油漆验收后", "amount": 30000},
    "installment_4": {"ratio": "5%", "trigger": "竣工验收后", "amount": 6000}
  },
  "warranty_clauses": {
    "hidden_works_years": null,
    "finish_works_years": null,
    "has_warranty_certificate": true
  },
  "penalty_clause": {
    "daily_penalty_rate": "0.1%",
    "max_penalty": "合同总额的5%"
  },
  "material_change_clause": "材料变更条款原文摘要",
  "arbitration_clause": "争议解决方式",
  "risky_clauses_summary": [
    {"clause": "条款摘要", "risk_type": "材料替换风险/付款不合理/违约金过低等"}
  ]
}"""

SUPERVISION_REPORT_SCHEMA = """{
  "doc_type": "supervision_report",
  "source_file": "文件名",
  "report_date": "报告日期 YYYY-MM-DD",
  "project_phase": "当前施工阶段（如水电、泥瓦等）",
  "issues_found": [
    {
      "issue": "问题描述",
      "location": "位置",
      "severity": "严重/中等/建议",
      "current_status": "已整改/整改中/待处理/新发现"
    }
  ],
  "general_assessment": "总体评价摘要（如：整体质量较好/存在多处隐患等）"
}"""

GENERAL_DOC_SCHEMA = """{
  "doc_type": "general",
  "source_file": "文件名",
  "document_summary": "文档内容概述（50字以内）",
  "key_points": [
    {"point": "关键信息1", "relevance": "与装修相关的程度：high/medium/low/none"}
  ],
  "is_renovation_related": true
}"""


def _get_output_schema(doc_type: str) -> str:
    """根据文档类型返回对应的输出 schema"""
    schema_map = {
        "quotation": BILL_SCHEMA,
        "contract": CONTRACT_SCHEMA,
        "supervision_report": SUPERVISION_REPORT_SCHEMA,
    }
    default = GENERAL_DOC_SCHEMA
    return schema_map.get(doc_type, default)


def build_extraction_system_prompt(doc_type: str) -> str:
    """构建文档提取的系统提示词

    Args:
        doc_type: 文档类型

    Returns:
        完整的系统提示词字符串
    """
    output_schema = _get_output_schema(doc_type)
    return EXTRACTION_SYSTEM_PROMPT.format(
        doc_type=doc_type,
        output_schema=output_schema,
    )


def build_extraction_user_message(document_text: str, filename: str) -> str:
    """构建文档提取的用户消息

    Args:
        document_text: 文档纯文本
        filename: 文件名

    Returns:
        用户消息字符串
    """
    return f"""请从以下装修文档中提取关键信息，生成结构化摘要。

文件名：{filename}

文档内容：
{document_text[:15000]}  # 限制长度为 15000 字符，避免 token 过多

请严格按照要求的 JSON 格式输出。"""


def _map_classification_to_doc_type(classifications_json: dict) -> str:
    """将文档分类器的分类结果映射为提取器使用的 doc_type

    Args:
        classifications_json: 文档分类器的分类结果

    Returns:
        提取器使用的文档类型
    """
    doc_type = classifications_json.get("doc_type", "unknown")

    # 文档分类器返回 quotation/contract/unknown
    # 映射到 extractor 使用的类型
    mapping = {
        "quotation": "quotation",
        "contract": "contract",
    }
    return mapping.get(doc_type, "general")


def extract_structured_summary_from_classification(
    classifications_json: dict,
) -> dict:
    """从文档分类结果中提取可能已有的结构化信息

    这是一种轻量级方法：当文档分类结果已经包含足够信息时，
    直接从中提取结构化摘要，避免额外的 LLM 调用。

    Args:
        classifications_json: 文档分类器的分类结果

    Returns:
        结构化摘要字典（可能较简略）
    """
    doc_type = _map_classification_to_doc_type(classifications_json)
    key_snippets = classifications_json.get("key_snippets", [])

    summary = {
        "doc_type": doc_type,
        "source_file": "",
        "_extraction_method": "from_classification",
        "_note": "基于文档分类结果的轻量级摘要，如需完整摘要请调用完整提取流程",
    }

    if doc_type == "contract":
        # 从 key_snippets 中提取可能的关键条款
        risky_clauses = []
        for snippet in key_snippets:
            risky_clauses.append({
                "clause": snippet[:200] if snippet else "",
                "risk_type": "待确认",
            })
        summary["risky_clauses_summary"] = risky_clauses
        summary["key_snippets_count"] = len(key_snippets)

    return summary


def is_extraction_needed(classification_suggestion: str) -> bool:
    """判断是否需要完整提取（基于文档分类的建议）

    Args:
        classification_suggestion: 分类器给出的建议

    Returns:
        是否需要完整提取
    """
    # 如果分类器建议分析，则需要完整提取
    return "建议分析" in classification_suggestion or "建议" in classification_suggestion