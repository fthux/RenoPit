"""
Document Classifier Service — 文档类型检测与内容分类
用于判断用户上传的合同/报价单文件的可分析性，并提取关键文本片段。
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """文档分类结果"""
    is_relevant: bool = False
    doc_type: str = "unknown"
    language: str = "unknown"
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    key_snippets: list[str] = field(default_factory=list)
    suggestion: str = ""


# ── 关键词词典 ────────────────────────────────────────────────────

# 合同类关键词（中文）
CONTRACT_KEYWORDS = [
    "装修合同", "施工合同", "装饰合同", "家装合同", "委托合同",
    "甲方", "乙方", "发包方", "承包方", "委托方", "被委托方", "业主", "施工方",
    "工程价款", "合同价款", "付款方式", "付款比例", "付款节点",
    "首付款", "预付款", "进度款", "中期款", "尾款", "质保金",
    "工期", "竣工", "交付", "验收", "验收标准",
    "质保", "保修", "维保", "售后服务", "售后",
    "违约金", "违约责任", "赔偿责任", "赔偿",
    "变更", "增项", "签证", "洽商",
    "材料清单", "工艺标准", "施工规范", "国标",
    "合同", "协议", "条款", "约定", "甲乙",
    "附件", "补充协议", "主材", "辅材",
    "交底", "水电定位", "隐蔽工程",
    "开工日期", "完工日期", "竣工日期", "工期延误",
]

# 报价类关键词（中文）
QUOTATION_KEYWORDS = [
    "报价单", "预算表", "预算清单", "报价明细", "费用清单", "决算",
    "项目名称", "工程量", "单价", "合价", "人工费", "材料费",
    "小计", "总计", "合计", "总价", "直接费", "管理费",
    "平米", "米", "项", "套", "个", "按", "一批",
    "拆旧", "拆除", "铲除", "垃圾清运", "清运",
    "水电", "泥瓦", "木工", "油漆", "油工", "安装",
    "防水", "贴砖", "铺贴", "墙砖", "地砖", "地板",
    "吊顶", "龙骨", "石膏板", "隔墙",
    "批刮", "腻子", "面漆", "底漆", "乳胶漆",
    "现场制作", "定制", "成品安装",
    "主材", "辅材", "损耗", "施工",
    "半包", "全包", "清包", "套餐",
    "折扣", "活动价", "优惠", "一口价",
    "不包含", "不含", "另计", "另算", "单独收费",
    "非标", "特殊规格", "进口", "高端", "升级",
    "实测实量", "按实结算",
    "设计费", "管理费", "远程费", "运输费", "上楼费",
]

# 金额模式（中文金额和阿拉伯数字金额）
AMOUNT_PATTERNS = [
    r'\d+\.?\d*\s*元',
    r'\d+\.?\d*\s*万',
    r'¥\s*\d+\.?\d*',
    r'人民币\s*\d+',
    r'单价\s*[:：]?\s*\d+',
    r'小计\s*[:：]?\s*\d+',
    r'合计\s*[:：]?\s*\d+',
    r'总价\s*[:：]?\s*\d+',
]

# 装修无关文件模式
IRRELEVANT_PATTERNS = [
    # 纯设计说明类（不含具体设计）
    r'本设计[^，]{0,20}主题[为是]',
    r'设计灵感来自于',
    r'设计风格[:：]\s*(现代简约|欧式|美式|中式|地中海|田园|北欧|轻奢|工业|新中式|日式|侘寂)',
    # 纯广告/营销文案
    r'关注公众号|扫码关注|加微信|朋友圈|转发',
    # 装修日记/分享（非正式文档）
    r'装修日记|装修记录|我的装修|新房装修|装修心得',
    # 效果图清单（纯图片目录）
    r'效果图\s*[1-9一-十]',
]


# ── 分类函数 ───────────────────────────────────────────────────────

def classify_document(text: str, filename: str = "") -> ClassificationResult:
    """对文档文本进行分类，判断是否为合同/报价单类文件

    Args:
        text: 文档提取的纯文本内容
        filename: 原始文件名（用于辅助判断）

    Returns:
        ClassificationResult 包含分类结果和建议
    """
    if not text or not text.strip():
        return ClassificationResult(
            is_relevant=False,
            doc_type="empty",
            language="unknown",
            confidence=0.0,
            reasons=["文档内容为空"],
            suggestion="文件内容为空，无法分析。请确认文件是否正确。",
        )

    text_lower = text.lower()
    reasons: list[str] = []
    key_snippets: list[str] = []

    # ── 判断是否包含大量中文装修相关内容 ──
    # 统计中文合同关键词命中
    contract_hits = sum(1 for kw in CONTRACT_KEYWORDS if kw in text)
    quotation_hits = sum(1 for kw in QUOTATION_KEYWORDS if kw in text)

    total_chars = len(text)
    contract_density = contract_hits / total_chars * 1000 if total_chars > 0 else 0
    quotation_density = quotation_hits / total_chars * 1000 if total_chars > 0 else 0

    # ── 提取金额信息 ──
    amount_matches = []
    for pattern in AMOUNT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amount_matches.extend(matches)

    has_amounts = len(amount_matches) > 0

    # ── 确定文档类型 ──
    doc_type = "unknown"
    confidence = 0.0

    if contract_hits >= 3:
        doc_type = "contract"
        if contract_hits >= 10:
            confidence = 0.90
        elif contract_hits >= 5:
            confidence = 0.75
        else:
            confidence = 0.60
        reasons.append(f"检测到 {contract_hits} 个合同相关关键词")
    elif quotation_hits >= 3:
        doc_type = "quotation"
        if quotation_hits >= 10:
            confidence = 0.90
        elif quotation_hits >= 5:
            confidence = 0.75
        else:
            confidence = 0.60
        reasons.append(f"检测到 {quotation_hits} 个报价相关关键词")

        if has_amounts:
            confidence = min(confidence + 0.10, 0.95)
            reasons.append(f"检测到 {len(amount_matches)} 处金额信息")
    elif has_amounts:
        # 有金额但没有明显报价关键词，可能是不规范的报价单
        doc_type = "quotation"
        confidence = 0.45
        reasons.append(f"检测到 {len(amount_matches)} 处金额信息，但报价关键词不足")
        reasons.append("文档格式可能不规范，建议确认是否为报价单")
    else:
        reasons.append("未检测到合同或报价相关关键词")

    # ── 检查是否是无关文档 ──
    for pattern in IRRELEVANT_PATTERNS:
        if re.search(pattern, text):
            reasons.append(f"文档内容疑似非正式装修文件（匹配模式: {pattern}）")
            doc_type = "irrelevant"
            confidence = max(confidence, 0.70)
            break

    # ── 判断是否为纯英文 ──
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0

    if chinese_ratio < 0.1:
        reasons.append("文档中中文内容占比过低，可能无法准确分析")

    language = "zh" if chinese_ratio >= 0.3 else "en" if chinese_ratio < 0.05 else "mixed"

    # ── 提取关键片段 ──
    key_snippets = _extract_snippets(text, doc_type)

    # ── 生成建议 ──
    suggestion = _generate_suggestion(doc_type, confidence)

    # ── 判断相关性 ──
    is_relevant = doc_type in ("contract", "quotation") and confidence >= 0.40
    if doc_type == "quotation" and confidence < 0.50:
        # 低置信度报价单仍然尝试分析，但添加警告
        is_relevant = True
        reasons.append("报价单置信度较低，分析结果仅供参考")

    logger.info(
        "[DocumentClassifier] 分类完成: file=%s, type=%s, confidence=%.2f, relevant=%s, reasons=%s",
        filename, doc_type, confidence, is_relevant, reasons,
    )

    return ClassificationResult(
        is_relevant=is_relevant,
        doc_type=doc_type,
        language=language,
        confidence=confidence,
        reasons=reasons,
        key_snippets=key_snippets,
        suggestion=suggestion,
    )


# ── 辅助函数 ────────────────────────────────────────────────────────

def _extract_snippets(text: str, doc_type: str, max_snippets: int = 3) -> list[str]:
    """从文档中提取与装修合同/报价相关的关键文本片段

    Args:
        text: 文档全文
        doc_type: 文档类型
        max_snippets: 最大片段数

    Returns:
        关键文本片段列表
    """
    snippets: list[str] = []

    if doc_type == "contract":
        # 付款方式
        for pattern in [
            r'(付款[方式比例节奏节点].*?(?:。|\n|$))',
            r'(首付.*?(?:。|\n|$))',
            r'(尾款.*?(?:。|\n|$))',
            r'(违约金.*?(?:。|\n|$))',
            r'(质保.*?(?:。|\n|$))',
            r'(验收.*?(?:。|\n|$))',
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                snippet = match.group(1).strip()[:200]
                if snippet not in snippets:
                    snippets.append(snippet)
                if len(snippets) >= max_snippets:
                    break

    elif doc_type == "quotation":
        # 金额相关行
        amount_lines = []
        for line in text.split('\n'):
            if re.search(r'[¥元]|合计|小计|单价|总价|总计', line):
                amount_lines.append(line.strip()[:200])
                if len(amount_lines) >= max_snippets:
                    break
        snippets = amount_lines

    return snippets


def _generate_suggestion(doc_type: str, confidence: float) -> str:
    """根据分类结果生成提示文本"""
    if doc_type == "empty":
        return "文件内容为空，无法分析。请确认文件是否正确。"
    elif doc_type == "irrelevant":
        return "该文件看起来不是装修合同或报价单，建议确认文件内容后再上传。"
    elif doc_type == "contract":
        if confidence >= 0.80:
            return "检测到装修合同文件，将分析合同条款中的风险项。"
        else:
            return "疑似装修合同，将尽力分析其中的风险条款。"
    elif doc_type == "quotation":
        if confidence >= 0.80:
            return "检测到装修报价单，将分析报价中的陷阱和增项风险。"
        else:
            return "疑似报价文件，将尽力分析其中的潜在陷阱。"
    else:
        return "无法确定文件类型，如果您确认是装修合同或报价单，可以继续分析。"