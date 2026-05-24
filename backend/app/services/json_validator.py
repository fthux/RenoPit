"""
JSON Validator Service — LLM 返回结果的校验与修复
支持 json_repair 自动修复、字段完整性校验、降级填充
"""

import json
from typing import Optional, Tuple, Dict, Any

from json_repair import repair_json


def _clean_markdown_fences(text: str) -> str:
    """移除 Markdown 代码围栏标记（```json 和 ```）"""
    t = text.strip()

    # 移除开头的 ```json 或 ```
    if t.startswith("```"):
        # 找到第一个换行符
        newline_idx = t.find("\n")
        if newline_idx != -1:
            t = t[newline_idx + 1 :]
        else:
            # 只有 ```，没有内容
            t = ""

    # 移除结尾的 ```
    if t.rstrip().endswith("```"):
        # 找到最后一个 ``` 前的位置
        last_triple = t.rstrip().rfind("```")
        if last_triple != -1:
            t = t[:last_triple]

    return t.strip()


def _extract_json_block(text: str) -> str:
    """尝试从文本中提取最外层的 JSON 对象 {}"""
    t = _clean_markdown_fences(text)

    # 找到第一个 { 和最后一个 }
    start = t.find("{")
    end = t.rfind("}")

    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]

    return t


def parse_json(text: str) -> Tuple[Optional[dict], Optional[str]]:
    """尝试解析 LLM 返回的 JSON

    执行顺序：
    1. 直接 json.loads()
    2. json_repair 修复后 json.loads()
    3. 都失败则返回 None

    Args:
        text: LLM 返回的原始文本

    Returns:
        (parsed_dict, error_message) 元组。
        成功时 error_message 为 None。
        失败时 parsed_dict 为 None。
    """
    if not text or not text.strip():
        return None, "LLM 返回空响应"

    # 先清理 Markdown 代码围栏
    cleaned = _extract_json_block(text)

    # 尝试 1：直接解析
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result, None
    except json.JSONDecodeError:
        pass

    # 尝试 2：json_repair 修复
    try:
        repaired = repair_json(cleaned)
        result = json.loads(repaired)
        if isinstance(result, dict):
            return result, None
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return None, f"JSON 解析失败（含 json_repair 修复）: {str(e)}"

    return None, "解析结果不是 JSON 对象"


def validate_structure(data: dict) -> Tuple[bool, list[str]]:
    """校验 JSON 字段完整性

    检查必需字段和关键约束：
    - problems 数组不能为空
    - summary 不能为空
    - 每个 problem 的 title 不能为空

    Args:
        data: 已解析的 JSON 字典

    Returns:
        (is_valid, missing_fields) 元组。
        is_valid: True 表示通过校验。
        missing_fields: 缺失/违规的字段列表。
    """
    issues: list[str] = []

    # 检查顶层字段
    if not data.get("summary"):
        issues.append("summary — 缺失或为空")

    problems = data.get("problems")
    if not problems or not isinstance(problems, list) or len(problems) == 0:
        issues.append("problems — 缺失或为空数组")
        return False, issues

    # 检查每个 problem 的字段
    for i, problem in enumerate(problems):
        if not isinstance(problem, dict):
            issues.append(f"problems[{i}] — 不是对象")
            continue

        if not problem.get("title"):
            issues.append(f"problems[{i}].title — 缺失或为空")

        # bbox 格式校验（可为 null、4 元素数组 [x1,y1,x2,y2]）
        bbox = problem.get("bbox")
        if bbox is not None:
            if not isinstance(bbox, list) or len(bbox) != 4:
                issues.append(f"problems[{i}].bbox — 格式不正确（应为 [x1,y1,x2,y2] 或 null）")
            else:
                for v in bbox:
                    if not isinstance(v, (int, float)):
                        issues.append(f"problems[{i}].bbox — 坐标值必须为数字")
                        break

    return len(issues) == 0, issues


def apply_fallback(data: dict) -> dict:
    """对缺失的非关键字段进行降级填充

    Args:
        data: 已解析的 JSON 字典

    Returns:
        填充后的字典
    """
    # 确保 summary 存在
    if not data.get("summary"):
        data["summary"] = "分析报告生成中，请查看详细问题列表。"

    # 确保 project_date 存在
    if "project_date" not in data:
        from datetime import datetime
        data["project_date"] = datetime.now().strftime("%Y-%m-%d")

    # 确保 problems 存在
    if "problems" not in data or not isinstance(data.get("problems"), list):
        data["problems"] = []

    # 对每个 problem 填充缺失字段
    for problem in data["problems"]:
        if not isinstance(problem, dict):
            continue

        if "title" not in problem or not problem.get("title"):
            problem["title"] = "未命名问题"

        if "location" not in problem or not problem.get("location"):
            problem["location"] = "未指定位置"

        if "critique" not in problem or not problem.get("critique"):
            problem["critique"] = "信息缺失"

        if "trap_explanation" not in problem or not problem.get("trap_explanation"):
            problem["trap_explanation"] = "信息缺失"

        if "alternative" not in problem or not problem.get("alternative"):
            problem["alternative"] = "信息缺失"

        # bbox 保持原样（null 或数组）

    return data


def validate_document_structure(data: dict) -> Tuple[bool, list[str]]:
    """校验文档分析 JSON 字段完整性

    检查必需字段和关键约束：
    - risks 数组不能为空
    - summary 不能为空
    - 每个 risk 的 title 和 original_text 不能为空

    Args:
        data: 已解析的 JSON 字典

    Returns:
        (is_valid, missing_fields) 元组。
    """
    issues: list[str] = []

    # 检查顶层字段
    if not data.get("summary"):
        issues.append("summary — 缺失或为空")

    if "total_estimated_risk" not in data:
        issues.append("total_estimated_risk — 缺失")

    risks = data.get("risks")
    if not risks or not isinstance(risks, list) or len(risks) == 0:
        issues.append("risks — 缺失或为空数组")
        return False, issues

    # 检查每个 risk 的字段
    for i, risk in enumerate(risks):
        if not isinstance(risk, dict):
            issues.append(f"risks[{i}] — 不是对象")
            continue

        if not risk.get("title"):
            issues.append(f"risks[{i}].title — 缺失或为空")

        if not risk.get("original_text"):
            issues.append(f"risks[{i}].original_text — 缺失或为空")

        if not risk.get("category"):
            issues.append(f"risks[{i}].category — 缺失")
        elif risk["category"] not in ("billing_trap", "contract_clause", "extra_item"):
            issues.append(f"risks[{i}].category — 未知类型 '{risk['category']}'")

        if not risk.get("id"):
            issues.append(f"risks[{i}].id — 缺失")

    return len(issues) == 0, issues


def apply_document_fallback(data: dict) -> dict:
    """对文档分析 JSON 缺失的非关键字段进行降级填充

    Args:
        data: 已解析的 JSON 字典

    Returns:
        填充后的字典
    """
    if not data.get("summary"):
        data["summary"] = "文档分析完成，请查看详细风险列表。"

    if "total_estimated_risk" not in data:
        data["total_estimated_risk"] = "暂无法估量"

    if "risks" not in data or not isinstance(data.get("risks"), list):
        data["risks"] = []

    for i, risk in enumerate(data.get("risks", [])):
        if not isinstance(risk, dict):
            continue

        if not risk.get("id"):
            risk["id"] = f"risk-{i + 1}"

        if "category" not in risk or not risk.get("category"):
            risk["category"] = "contract_clause"

        if "title" not in risk or not risk.get("title"):
            risk["title"] = f"未命名风险 #{i + 1}"

        if "original_text" not in risk or not risk.get("original_text"):
            risk["original_text"] = "（原文无法定位）"

        if "critique" not in risk or not risk.get("critique"):
            risk["critique"] = "信息缺失，暂无法提供批判分析"

        if "financial_consequence" not in risk or not risk.get("financial_consequence"):
            risk["financial_consequence"] = "暂无法估量"

        if "suggested_fix" not in risk or not risk.get("suggested_fix"):
            risk["suggested_fix"] = "当前信息不足，请进一步确认合同条款"

    return data


def validate_document_report(llm_response_text: str) -> Tuple[Optional[dict], Optional[str]]:
    """文档分析 JSON 完整的校验与修复流程

    解析 → 校验 → 降级填充

    Args:
        llm_response_text: LLM 返回的原始文本

    Returns:
        (result_dict, error_message) 元组。
    """
    # Step 1: 解析 JSON
    data, parse_error = parse_json(llm_response_text)
    if data is None:
        return None, parse_error

    # Step 2: 字段完整性校验
    is_valid, issues = validate_document_structure(data)

    if not is_valid:
        risks = data.get("risks", [])
        if not risks or not isinstance(risks, list) or len(risks) == 0:
            return None, f"文档 JSON 校验失败 — 关键信息缺失: {', '.join(issues)}"

    # Step 3: 降级填充
    data = apply_document_fallback(data)

    if not data.get("risks"):
        return None, "文档 JSON 校验失败 — risks 数组为空"

    return data, None


def validate_and_repair(llm_response_text: str) -> Tuple[Optional[dict], Optional[str]]:
    """完整的校验与修复流程

    对外统一接口：解析 → 校验 → 降级填充

    Args:
        llm_response_text: LLM 返回的原始文本

    Returns:
        (result_dict, error_message) 元组。
        - 完全成功：result_dict 为修复后的完整 JSON，error_message 为 None
        - 关键字段缺失：result_dict 为 None，error_message 包含错误信息
        - 解析失败：result_dict 为 None，error_message 包含错误信息
    """
    # Step 1: 解析 JSON
    data, parse_error = parse_json(llm_response_text)
    if data is None:
        return None, parse_error

    # Step 2: 字段完整性校验
    is_valid, issues = validate_structure(data)

    if not is_valid:
        # 检查是否是关键字段缺失（problems 数组为空）
        problems = data.get("problems", [])
        if not problems or not isinstance(problems, list) or len(problems) == 0:
            return None, f"JSON 校验失败 — 关键字段缺失: {', '.join(issues)}"

        # 非关键字段缺失可降级填充后继续
        # 但仍记录 issue
        pass

    # Step 3: 降级填充
    data = apply_fallback(data)

    # 填充后再次确认 problems 不为空
    if not data.get("problems"):
        return None, "JSON 校验失败 — problems 数组为空"

    return data, None