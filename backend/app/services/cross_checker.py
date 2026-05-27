"""
Cross Checker — 多文档交叉比对引擎
两阶段流水线：
  阶段1: 对每份文档提取结构化摘要（token 压缩）
  阶段2: 合并所有摘要，调用交叉比对 Prompt → 输出差异报告

支持以下比对模式：
- BILL_vs_CONTRACT: 合同范围 vs 报价单项
- SUPERVISION_TRACKING: 多期报告问题追踪
- DESIGN_vs_BILL: 设计工艺要求 vs 报价工艺描述
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# 比对模式说明（不含三元表达式，由 build_cross_check_system_prompt 构建）
# ============================================================

_MODE_DESCRIPTIONS = {
    "BILL_vs_CONTRACT": """【合同 vs 报价单】比对要点：
- 合同约定的施工范围是否在报价单中有对应的项目？
- 合同中的材料品牌/型号是否与报价单一致？
- 合同约定的付款比例是否与报价单吻合？
- 报价单中是否包含合同要求但未列出的隐蔽工程或工艺要求？
- 需要特别标注'合同有但报价无'和'报价有但合同未承诺'两种不同风险""",

    "SUPERVISION_TRACKING": """【多期监理报告】比对要点：
- 对多期报告中的问题列表进行逐项追踪
- 同一问题在后续报告中是否标记为已整改？
- 未闭环的问题在当期报告中是否仍然存在？
- 新出现的问题是否与之前的问题有关联？""",

    "DESIGN_vs_BILL": """【设计说明 vs 报价单】比对要点：
- 设计说明中的工艺要求是否与报价单中的工艺描述一致？
- 是否有'降级施工'的情况（设计要求薄贴法，报价写水泥砂浆）？
- 设计中要求使用的材料品牌/规格是否在报价单中有对应？""",
}

# ============================================================
# 交叉比对系统提示词模板（使用 {{mode_description}} 占位符）
# ============================================================

CROSS_CHECK_SYSTEM_PROMPT = """你是一位收了消费者高额咨询费的专业家装监理兼合同审核专家。你的任务是**对比多份装修相关文档的结构化摘要**，找出文档之间存在的**差异、矛盾和不一致之处**。

## 比对模式：{check_mode}

### 核心原则
1. **只输出跨文档的差异项**：单份文档自身的问题（如一份报价单的漏项）不属于交叉核查范围
2. **每项差异必须有明确依据**：需要引用两份文档中各自的具体内容
3. **区分差异类型**：范围缺失、材料替换、工艺降级、付款矛盾等

### 比对模式说明

{mode_description}

## 输出要求

严格按照以下 JSON 结构输出：

```json
{{
  "check_mode": "{check_mode}",
  "document_pairs": ["文件A名称", "文件B名称"],
  "pair_type": "BILL_vs_CONTRACT | SUPERVISION_TRACKING | DESIGN_vs_BILL",
  "discrepancies": [
    {{
      "type": "scope_mismatch | material_substitution | payment_inconsistency | process_downgrade | price_discrepancy | supervision_tracking | other",
      "severity": "high | medium | low",
      "description": "差异描述，明确说明两份文档之间的不一致之处",
      "source_a": "来源文件A中的具体位置引用",
      "source_b": "来源文件B中的具体位置引用或说明",
      "risk": "这个差异可能导致的后果",
      "suggested_action": "建议业主如何处理这个差异"
    }}
  ]
}}
```

注意：
1. 如果未发现任何不一致项，输出空的 discrepancies 列表并在 summary 中说明
2. 每个差异项必须明确标注严重等级
3. source_a 和 source_b 必须引用具体内容（不是简单的文件名）
4. 对于监理报告追踪模式，还需附加 supervision_tracking 字段"""

SUPERVISION_TRACKING_PROMPT = """你是一位收了消费者高额咨询费的专业家装监理。你的任务是**追踪多期监理报告中发现的问题整改进度**。

## 输入数据

以下是多期监理报告的结构化摘要（按时间顺序排列）：

{reports_summaries}

## 追踪要求

1. 对比各期报告中 issues_found 列表，找出同一问题在不同期的状态变化
2. 问题匹配依据：问题描述相似性（同一位置 + 同一类型问题）
3. 标记每个问题的最终状态

## 输出格式

```json
{{
  "total_issues_found": 12,
  "resolved": 8,
  "unresolved": 4,
  "unresolved_items": [
    {{
      "issue": "问题描述",
      "first_reported": "报告1名称",
      "last_reported": "报告3名称",
      "status": "unresolved",
      "severity": "high | medium | low",
      "risk": "问题得不到解决可能导致的后果"
    }}
  ],
  "resolved_items": [
    {{
      "issue": "问题描述",
      "first_reported": "报告1名称",
      "resolved_in": "报告2名称",
      "resolution": "整改结果"
    }}
  ]
}}
```"""


# ============================================================
# 比对模式检测
# ============================================================

def detect_check_mode(doc_summaries: list[dict]) -> str:
    """根据文档摘要列表自动检测应该使用的比对模式

    Args:
        doc_summaries: 文档结构化摘要列表

    Returns:
        检测到的比对模式
    """
    if not doc_summaries or len(doc_summaries) < 2:
        return "UNKNOWN"

    doc_types = [d.get("doc_type", "general") for d in doc_summaries]

    # 合同 vs 报价单
    if "contract" in doc_types and "quotation" in doc_types:
        return "BILL_vs_CONTRACT"

    # 多期监理报告（≥2 份监理报告）
    supervision_reports = [d for d in doc_summaries if d.get("doc_type") == "supervision_report"]
    if len(supervision_reports) >= 2:
        return "SUPERVISION_TRACKING"

    # 设计说明 vs 报价单
    if "general" in doc_types and "quotation" in doc_types:
        return "DESIGN_vs_BILL"

    # 默认：混合比对（尽可能识别）
    return "BILL_vs_CONTRACT"


def build_cross_check_user_message(doc_summaries: list[dict]) -> str:
    """构建交叉比对用户消息

    Args:
        doc_summaries: 文档结构化摘要列表

    Returns:
        用户消息字符串
    """
    parts = ["以下是多份文档的结构化摘要，请对比分析它们之间的不一致之处：\n"]

    for i, summary in enumerate(doc_summaries):
        source = summary.get("source_file", f"文档{i+1}")
        parts.append(f"\n--- 文档 {i+1}: {source} ---")
        parts.append(json.dumps(summary, ensure_ascii=False, indent=2))

    # 附加已存在的风险分析结果（如果有）
    risk_summaries = []
    for summary in doc_summaries:
        if "risks_json" in summary and summary["risks_json"]:
            risks = summary["risks_json"].get("risks", [])
            summary_text = summary["risks_json"].get("summary", "")
            risk_summaries.append(
                f"  - 文件 {summary.get('source_file', '未知')}:\n"
                f"    分析摘要: {summary_text}\n"
                f"    风险数量: {len(risks)} 项\n"
                f"    预估总风险: {summary['risks_json'].get('total_estimated_risk', 'N/A')}"
            )

    if risk_summaries:
        parts.append("\n\n--- 单文件风险分析摘要（供参考） ---")
        parts.extend(risk_summaries)
        parts.append("\n（注意：以上单文件分析结果仅供参考，交叉核查应当聚焦于差异本身）")

    return "\n".join(parts)


def build_supervision_tracking_user_message(report_summaries: list[dict]) -> str:
    """构建监理报告追踪的用户消息

    Args:
        report_summaries: 监理报告的结构化摘要列表

    Returns:
        用户消息字符串
    """
    formatted = []
    for i, summary in enumerate(report_summaries):
        source = summary.get("source_file", f"监理报告{i+1}")
        date = summary.get("report_date", "日期未知")
        phase = summary.get("project_phase", "阶段未知")
        issues = summary.get("issues_found", [])

        formatted.append(
            f"### {source}（{date}，阶段：{phase}）\n"
        )

        if not issues:
            formatted.append("- 本期报告未发现问题\n")
        else:
            for j, issue in enumerate(issues):
                formatted.append(
                    f"{j+1}. [{issue.get('severity', '未知')}] {issue.get('issue', '')}\n"
                    f"   位置：{issue.get('location', '未知')}\n"
                    f"   状态：{issue.get('current_status', '未标记')}\n"
                )

    return "\n".join(formatted)


def build_cross_check_system_prompt(check_mode: str) -> str:
    """构建交叉比对系统提示词

    将模式相关的比对要点从代码中注入模板，避免模板内的三元表达式
    被 str.format() 错误解析。

    Args:
        check_mode: 比对模式

    Returns:
        完整的系统提示词字符串
    """
    mode_description = _MODE_DESCRIPTIONS.get(check_mode, "")

    # 对字符串中的 { 和 } 进行安全处理
    # CROSS_CHECK_SYSTEM_PROMPT 中的 JSON 示例使用了 {{ 和 }} 进行转义
    # 但 mode_description 可能包含 { 或 }，需要先转义
    mode_description = mode_description.replace("{", "{{").replace("}", "}}")

    return CROSS_CHECK_SYSTEM_PROMPT.format(
        check_mode=check_mode,
        mode_description=mode_description,
    )


def build_supervision_tracking_system_prompt() -> str:
    """构建监理报告追踪的系统提示词

    Returns:
        完整的系统提示词字符串
    """
    return SUPERVISION_TRACKING_PROMPT.format(
        reports_summaries="（见用户输入）"
    )