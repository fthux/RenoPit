"""
PDF Generation Service
Generates a downloadable PDF report for renovation analysis results.

Key fixes:
1. Uses extracted TTF font (not .ttc) to avoid reportlab's CJK rendering bug
2. Properly embeds uploaded images into the PDF
3. Draws bounding box annotations on images for better visual feedback
4. Properly sanitizes HTML entities to avoid ReportLab XML parsing errors

Data flow:
- The `generate_pdf()` function accepts pre-computed `result_data` and `images_data`
  from the API layer, ensuring data processing logic is consistent with the
  `/api/projects/{project_id}/result` endpoint.
"""

import io
import logging
import os
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# ── Font Path (bundled extracted TTF) ──────────────────────────────
# __file__ = backend/app/services/pdf_generator.py
# dirname x3 -> backend/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
_FONT_PATH = os.path.join(_FONT_DIR, "STHeitiLight-extracted.ttf")

_CN_FONT = "STHeiti"
_BOLD_CN_FONT = "STHeiti-Bold"

def _ensure_font_registered():
    """Register the Chinese font if not already done."""
    if _CN_FONT not in pdfmetrics._fonts:
        try:
            if os.path.exists(_FONT_PATH):
                pdfmetrics.registerFont(TTFont(_CN_FONT, _FONT_PATH))
                logger.info(f"Registered Chinese font from {_FONT_PATH}")
            else:
                logger.warning(f"Chinese font not found at {_FONT_PATH}, will use Helvetica")
        except Exception as e:
            logger.warning(f"Failed to register Chinese font: {e}")


# ── Color palette ──────────────────────────────────────────────────
_COLORS = {
    "primary": "#1E3A5F",
    "accent": "#2DD4A0",
    "critical": "#DC2626",
    "high": "#EA580C",
    "medium": "#CA8A04",
    "low": "#2563EB",
    "bg_light": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "text": "#1E293B",
    "text_muted": "#94A3B8",
    "border": "#E2E8F0",
    "bg_critical": "#FEF2F2",
    "bg_high": "#FFF7ED",
    "bg_medium": "#FEFCE8",
    "bg_low": "#EFF6FF",
}

_SEVERITY_COLORS = {
    "critical": (_COLORS["critical"], _COLORS["bg_critical"]),
    "high": (_COLORS["high"], _COLORS["bg_high"]),
    "medium": (_COLORS["medium"], _COLORS["bg_medium"]),
    "low": (_COLORS["low"], _COLORS["bg_low"]),
}

# ── Styles ─────────────────────────────────────────────────────────
def _styles():
    _ensure_font_registered()
    use_font = _CN_FONT if _CN_FONT in pdfmetrics._fonts else "Helvetica"
    return {
        "use_font": use_font,
        "title": ParagraphStyle("Title", fontName=use_font, fontSize=26, leading=34,
                                textColor=colors.HexColor(_COLORS["primary"]),
                                spaceAfter=6, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("Subtitle", fontName=use_font, fontSize=10, leading=14,
                                   textColor=colors.HexColor(_COLORS["text_muted"]),
                                   spaceAfter=20, alignment=TA_LEFT),
        "h1": ParagraphStyle("H1", fontName=use_font, fontSize=18, leading=24,
                             textColor=colors.HexColor(_COLORS["primary"]),
                             spaceBefore=16, spaceAfter=8, alignment=TA_LEFT),
        "h2": ParagraphStyle("H2", fontName=use_font, fontSize=14, leading=20,
                             textColor=colors.HexColor(_COLORS["primary"]),
                             spaceBefore=12, spaceAfter=6, alignment=TA_LEFT),
        "h3": ParagraphStyle("H3", fontName=use_font, fontSize=11, leading=16,
                              textColor=colors.HexColor(_COLORS["text"]),
                              spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName=use_font, fontSize=9, leading=14,
                               textColor=colors.HexColor(_COLORS["text"]),
                               spaceAfter=6, alignment=TA_JUSTIFY),
        "body_small": ParagraphStyle("BodySmall", fontName=use_font, fontSize=8.5, leading=12,
                                     textColor=colors.HexColor(_COLORS["text"]),
                                     spaceAfter=4, alignment=TA_LEFT),
        "caption": ParagraphStyle("Caption", fontName=use_font, fontSize=7, leading=10,
                                  textColor=colors.HexColor(_COLORS["text_muted"]),
                                  spaceAfter=2, alignment=TA_CENTER),
        "footer": ParagraphStyle("Footer", fontName=use_font, fontSize=8, leading=11,
                                 textColor=colors.HexColor(_COLORS["text_muted"]),
                                 alignment=TA_CENTER),
        "cell_severity": ParagraphStyle("CellSev", fontName=use_font, fontSize=8, leading=10,
                                        textColor=colors.white, alignment=TA_CENTER,
                                        spaceBefore=2, spaceAfter=2),
    }


def _severity_label(sev):
    return {"critical": "严重", "high": "高", "medium": "中", "low": "低"}.get(sev, sev)


def _build_content(project_id: str, analysis_data: dict, images_data: list, document_analyses_data: Optional[dict] = None) -> list:
    """Build the document content (list of flowables)."""
    S = _styles()
    story = []

    # ── Cover Page ─────────────────────────────────────────────
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("装修避坑分析报告", S["title"]))
    story.append(Paragraph("Renovation Pitfall Analysis Report", S["subtitle"]))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("基本信息", S["h1"]))
    story.append(Paragraph(f"所属项目编号：{project_id}", S["body"]))
    story.append(Paragraph(f"分析报告编号：{analysis_data.get('id', 'N/A')}", S["body"]))
    story.append(Paragraph(f"分析开始日期：{analysis_data.get('created_at', 'N/A')[:19]}", S["body"]))
    story.append(Paragraph(f"分析完成日期：{analysis_data.get('completed_at', 'N/A')[:19]}", S["body"]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("综合评分", S["h1"]))
    summary = analysis_data.get("summary", {})
    score = int(summary.get("score", 0))
    story.append(_build_score_card(score))
    story.append(Spacer(1, 16 * mm))

    # Summary text
    summary_text = summary.get("summary_text", "")
    if summary_text:
        story.append(Paragraph("总体评估", S["h1"]))
        story.append(Paragraph(_sanitize_html(summary_text), S["body"]))
        story.append(Spacer(1, 4 * mm))

    # ── Compact severity row ───────────────────────────────────
    sev_order = ["critical", "high", "medium", "low"]
    sev_labels_map = {"critical": "严重", "high": "高", "medium": "中", "low": "低"}
    sev_colors_map = {"critical": _COLORS["critical"], "high": _COLORS["high"], "medium": _COLORS["medium"], "low": _COLORS["low"]}
    sev_count = {s: summary.get(f"{s}_count", 0) for s in sev_order}
    total = sum(sev_count.values())

    # Severity count labels (single instance, summary_text already covers the topic)
    header_parts = []
    for s in sev_order:
        c = sev_count.get(s, 0)
        header_parts.append(
            f'<font color="{sev_colors_map[s]}"><b>{sev_labels_map[s]}: {c}</b></font>'
        )
    if header_parts:
        story.append(Paragraph(
            " | ".join(header_parts),
            ParagraphStyle("SevRow", parent=S["body"], spaceAfter=6),
        ))

    # Distribution bar as a single table row with colored columns
    if total > 0:
        bar_cells = []
        bar_widths = []
        for s in sev_order:
            c = sev_count.get(s, 0)
            w = max(c / total * 200, 3 if c > 0 else 0)  # scale to 200pt
            bar_widths.append(w * mm if w > 0 else 0)
            if w > 0:
                bar_cells.append("")
        if bar_cells:
            from reportlab.platypus import Table
            if bar_cells:
                bar_data = [bar_cells]
                # Actually build a proper bar: one row with colored bg
                table_data = []
                table_widths = []
                for s in sev_order:
                    c = sev_count.get(s, 0)
                    if c > 0:
                        w = max(c / total * 170, 3)  # scale to 170mm
                        table_widths.append(w * mm)
                        table_data.append("")
                if table_data:
                    # Use a simple 1xN table for the bar
                    table_data = [["" for _ in table_widths]]
                    bar = Table(table_data, colWidths=table_widths, rowHeights=[8])
                    bar_styles = []
                    idx = 0
                    for s in sev_order:
                        c = sev_count.get(s, 0)
                        if c > 0:
                            bar_styles.append(("BACKGROUND", (idx, 0), (idx, 0), colors.HexColor(sev_colors_map[s])))
                            idx += 1
                    bar_styles.extend([
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ])
                    bar.setStyle(TableStyle(bar_styles))
                    story.append(Spacer(1, 2 * mm))
                    story.append(bar)
                    story.append(Spacer(1, 4 * mm))

    # ── Pitfalls Section ───────────────────────────────────────
    pitfalls = analysis_data.get("pitfalls", [])
    if not pitfalls:
        problems_raw = analysis_data.get("result_json", {}).get("problems", [])
        if problems_raw:
            pitfalls = []
            for i, p in enumerate(problems_raw):
                sev = p.get("severity", "medium")
                pitfalls.append({
                    "id": str(i + 1),
                    "category": p.get("category", "其他"),
                    "description": p.get("title", p.get("critique", "")),
                    "severity": sev,
                    "location": p.get("location", ""),
                    "suggestion": p.get("alternative", ""),
                    "critique": p.get("critique", ""),
                    "trap_explanation": p.get("trap_explanation", ""),
                })

    story.append(Paragraph("问题详情", S["h1"]))
    story.append(Paragraph(f"共发现 {len(pitfalls)} 个装修陷阱", S["body"]))
    story.append(Spacer(1, 4 * mm))

    for item in pitfalls:
        story.append(_build_pitfall_card(item, S))
        story.append(Spacer(1, 4 * mm))

    story.append(PageBreak())

    # ── Document Risk Analysis Section ────────────────────────────
    if document_analyses_data:
        story.append(Paragraph("合同 / 报价单风险分析", S["h1"]))
        story.append(Paragraph("以下为 AI 对上传的合同、报价单等文档进行的风险检测分析：", S["body"]))
        story.append(Spacer(1, 4 * mm))

        # Sort: latest first by created_at
        sorted_docs = sorted(document_analyses_data.values(), key=lambda x: x.get("created_at", ""), reverse=True)
        for doc in sorted_docs:
            story = _build_document_risk_section(story, doc, S)
            story.append(Spacer(1, 4 * mm))

        # Extra Item Prediction Section
        for doc in sorted_docs:
            extra_prediction = doc.get("extra_item_prediction")
            if extra_prediction:
                story.append(Paragraph("增项预测与总花费估算", S["h1"]))
                story.append(Paragraph("以下为 AI 基于报价单分析结果预测的施工过程中可能追加的增项：", S["body"]))
                story.append(Spacer(1, 4 * mm))
                story = _build_extra_prediction_section(story, extra_prediction, S)
                story.append(Spacer(1, 4 * mm))
                break  # Only render one prediction section

        story.append(PageBreak())


    # ── Design Images Section ──────────────────────────────────
    if images_data:
        story.append(Paragraph("设计图纸", S["h1"]))
        story.append(Paragraph("以下为项目上传的设计图纸及 AI 检测标注：", S["body"]))
        story.append(Spacer(1, 4 * mm))
        for idx, img_info in enumerate(images_data):
            story.append(_build_image_section(img_info, analysis_data, idx))
            story.append(Spacer(1, 6 * mm))

        story.append(PageBreak())

    return story


def _build_score_card(score: int):
    """Build a score visualization — flat table, no nested tables to avoid artifacts."""
    _ensure_font_registered()
    use_font = _CN_FONT if _CN_FONT in pdfmetrics._fonts else "Helvetica"

    color = _COLORS["accent"]
    if score < 60:
        color = _COLORS["high"]
    elif score < 80:
        color = _COLORS["medium"]

    score_text = Paragraph(
        f'<font size="48" color="{color}"><b>{score}</b></font>'
        f'<font size="14" color="{_COLORS["text_muted"]}"> / 100</font>',
        ParagraphStyle("ScoreLine", fontName=use_font, alignment=TA_CENTER, spaceAfter=8),
    )
    label_text = Paragraph(
        f'<font size="13" color="{color}"><b>'
        f'{"优秀" if score >= 80 else "待改进" if score >= 60 else "需重视"}'
        f'</b></font>',
        ParagraphStyle("ScoreLabel", fontName=use_font, alignment=TA_CENTER, spaceAfter=4),
    )

    # Single flat progress bar: fill on left, remaining on right
    fill_w = max(int(score * 1.6), 3)  # max 160 for score 100
    remain_w = max(160 - fill_w, 0)
    bar = Table(
        [["", ""]],
        colWidths=[fill_w, remain_w],
        rowHeights=[10],
    )
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(color)),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Wrap in a table for centering (no LINEBELOW styles)
    card = Table(
        [[score_text], [Spacer(1, 12 * mm)], [label_text], [Spacer(1, 6 * mm)], [bar]],
        colWidths=[200],
    )
    card.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return card


def _build_image_section(img_info: dict, analysis_data: dict, idx: int):
    """Build a section showing an image with optional bbox annotations."""
    S = _styles()
    elements = []

    # Title
    original_name = img_info.get("original_name", img_info.get("original_filename", f"图片{idx+1}"))
    elements.append(Paragraph(f"📷 {_sanitize_html(original_name)}", S["h1"]))
    elements.append(Spacer(1, 2 * mm))

    # Check if image file exists
    storage_path = img_info.get("storage_path", "")
    if storage_path and not os.path.isabs(storage_path):
        storage_path = os.path.abspath(storage_path)
    if not storage_path or not os.path.exists(storage_path):
        logger.warning(f"Image file not found: storage_path={storage_path}, original={original_name}")
        elements.append(Paragraph(f"[图片文件 {_sanitize_html(original_name)} 未找到]", S["body"]))
        return KeepTogether(elements)

    # Try to read image dimensions for fitting
    try:
        from PIL import Image as PILImage
        with PILImage.open(storage_path) as pil_img:
            img_w, img_h = pil_img.size
    except Exception:
        img_w, img_h = 800, 600

    # Fit image to PDF page width (with margins)
    max_w = 160 * mm
    max_h = 120 * mm
    aspect = img_w / img_h
    if img_w > max_w or img_h > max_h:
        if aspect > 1:
            display_w = max_w
            display_h = max_w / aspect
        else:
            display_h = max_h
            display_w = max_h * aspect
    else:
        display_w = img_w
        display_h = img_h

    try:
        pdf_img = Image(storage_path, width=display_w, height=display_h)
        elements.append(pdf_img)
    except Exception as e:
        logger.warning(f"Could not embed image {storage_path}: {e}")
        elements.append(Paragraph(f"[图片 {_sanitize_html(original_name)} 无法嵌入 PDF: {e}]", S["body"]))
        return KeepTogether(elements)

    # Try to find bbox annotations for this image
    pitfalls = analysis_data.get("pitfalls", [])
    problems_raw = analysis_data.get("result_json", {}).get("problems", [])
    all_items = pitfalls + problems_raw

    img_filename_lower = original_name.lower()
    related_bboxes = []
    for item in all_items:
        if not isinstance(item, dict):
            continue
        bbox = item.get("bbox")
        if bbox and isinstance(bbox, list) and len(bbox) == 4:
            location = (item.get("location") or "").lower()
            if img_filename_lower.split(".")[0] in location or location in img_filename_lower:
                try:
                    bbox_f = [float(x) for x in bbox]
                    scale_x = display_w / img_w
                    scale_y = display_h / img_h
                    bbox_display = [
                        bbox_f[0] * scale_x,
                        bbox_f[1] * scale_y,
                        bbox_f[2] * scale_x if len(bbox_f) > 2 else 0,
                        bbox_f[3] * scale_y if len(bbox_f) > 3 else 0,
                    ]
                    related_bboxes.append(bbox_display)
                except (ValueError, TypeError, IndexError):
                    pass

    if not related_bboxes:
        elements.append(Paragraph("（该图片未检测到具体问题位置）", S["caption"]))
    else:
        for item in all_items:
            if item.get("bbox") and isinstance(item.get("bbox"), list):
                location = (item.get("location") or "").lower()
                if img_filename_lower.split(".")[0] in location or location in img_filename_lower:
                    sev = item.get("severity", "medium")
                    desc = item.get("title", item.get("description", item.get("critique", "")))
                    if desc:
                        color = _SEVERITY_COLORS.get(sev, (_COLORS["text"], _COLORS["bg_light"]))[0]
                        elements.append(Paragraph(
                            f'<font color="{color}">■</font> '
                            f'<font color="{_COLORS["text"]}"><b>[{_severity_label(sev)}]</b> {_sanitize_html(desc)}</font>',
                            S["body_small"],
                        ))

    return KeepTogether(elements)


def _build_pitfall_card(item: dict, S: dict):
    """Build a card for one pitfall item."""
    sev = item.get("severity", "medium") or "medium"
    if sev not in _SEVERITY_COLORS:
        sev = "medium"
    sev_color, sev_bg = _SEVERITY_COLORS.get(sev, (_COLORS["text"], _COLORS["bg_light"]))
    sev_label = _severity_label(sev)
    description = item.get("description") or ""
    category = item.get("category", "其他") or "其他"
    location = item.get("location") or ""
    suggestion = item.get("suggestion") or ""
    critique = item.get("critique") or ""
    trap_explanation = item.get("trap_explanation") or ""

    card_data = []

    # Header row
    cell_header = ParagraphStyle("ch", parent=S["h3"], spaceBefore=0, spaceAfter=0)
    header_text = (
        f'<font color="{sev_color}">●</font> '
        f'<font color="{sev_color}"><b>[{sev_label}]</b></font> '
        f'<font color="{_COLORS["text"]}">{_sanitize_html(description)}</font>'
    )
    card_data.append([Paragraph(header_text, cell_header)])

    # Info row
    info_parts = [f'<font color="{_COLORS["text_muted"]}">分类：{_sanitize_html(category)}</font>']
    if location:
        info_parts.append(f'<font color="{_COLORS["text_muted"]}"> | 位置：{_sanitize_html(location)}</font>')
    info_text = "".join(info_parts)
    card_data.append([Paragraph(info_text, S["body_small"])])

    # Critique
    if critique:
        card_data.append([
            Paragraph(
                f'<font color="{_COLORS["text_muted"]}"><b>问题分析：</b>{_sanitize_html(critique)}</font>',
                S["body_small"],
            )
        ])

    # Trap Explanation
    if trap_explanation:
        card_data.append([
            Paragraph(
                f'<font color="{_COLORS["critical"]}"><b>陷阱说明：</b></font>'
                f'<font color="{_COLORS["text"]}">{_sanitize_html(trap_explanation)}</font>',
                S["body_small"],
            )
        ])

    # Suggestion
    if suggestion:
        card_data.append([
            Paragraph(
                f'<font color="{_COLORS["accent"]}"><b>✓ 建议：</b></font>'
                f'<font color="{_COLORS["text"]}">{_sanitize_html(suggestion)}</font>',
                S["body_small"],
            )
        ])

    card = Table(card_data, colWidths=[170 * mm])
    bg_color = colors.HexColor(sev_bg)
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(sev_color)),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(_COLORS["border"])),
    ]))
    return card


def _build_document_risk_section(story: list, doc: dict, S: dict) -> list:
    """Build a section for one document's risk analysis in the PDF.

    The `doc` dict uses the serialized format from _serialize_document_analyses(),
    with fields: doc_type, confidence, summary, total_estimated_risk, risks, etc.
    """
    # Determine document type label
    doc_type = doc.get("doc_type", "unknown")
    doc_type_label = {"quotation": "报价单", "contract": "合同"}.get(doc_type, "文档")

    # No overall_risk field — derive from risks count
    risks = doc.get("risks", []) or []
    risks_count = len(risks)
    summary_text = doc.get("summary", "")
    total_estimated_risk = doc.get("total_estimated_risk", "")
    created_at = doc.get("created_at", "")[:19]

    # Compute overall severity from risk count
    if risks_count >= 5:
        overall_risk = "high"
    elif risks_count >= 2:
        overall_risk = "medium"
    else:
        overall_risk = "low"

    risk_colors = {
        "high": _COLORS["critical"],
        "medium": _COLORS["medium"],
        "low": _COLORS["low"],
    }
    risk_labels = {"high": "高风险", "medium": "中风险", "low": "低风险"}
    risk_color = risk_colors.get(overall_risk, _COLORS["text_muted"])
    risk_label = risk_labels.get(overall_risk, overall_risk)

    header_text = (
        f'<font color="{risk_color}"><b>📄 {_sanitize_html(doc_type_label)}</b></font> '
        f'<font color="{_COLORS["text_muted"]}">| 风险等级：</font>'
        f'<font color="{risk_color}"><b>{risk_label}</b></font>'
        f'<font color="{_COLORS["text_muted"]}"> | 风险数：{risks_count} | {created_at}</font>'
    )
    story.append(Paragraph(header_text, S["body"]))
    story.append(Spacer(1, 2 * mm))

    # Summary text
    if summary_text:
        story.append(Paragraph(
            f'<font color="{_COLORS["text"]}">{_sanitize_html(summary_text)}</font>',
            S["body_small"],
        ))
        story.append(Spacer(1, 2 * mm))

    # Total estimated risk
    if total_estimated_risk:
        story.append(Paragraph(
            f'<font color="{_COLORS["critical"]}"><b>预估总风险：{_sanitize_html(total_estimated_risk)}</b></font>',
            S["body_small"],
        ))
        story.append(Spacer(1, 2 * mm))

    if not risks:
        story.append(Paragraph(
            f'<font color="{_COLORS["text_muted"]}">未检测到具体风险条款</font>',
            S["body_small"],
        ))
        story.append(Spacer(1, 2 * mm))
        return story

    # Category labels
    category_labels = {
        "billing_trap": "报价陷阱",
        "contract_clause": "合同条款",
        "extra_item": "增项风险",
    }
    category_colors = {
        "billing_trap": _COLORS["critical"],
        "contract_clause": _COLORS["high"],
        "extra_item": _COLORS["medium"],
    }

    for item in risks:
        item_category = item.get("category", "contract_clause")
        item_title = item.get("title", "")
        item_original_text = item.get("original_text", "")
        item_critique = item.get("critique", "")
        item_financial_consequence = item.get("financial_consequence", "")
        item_suggested_fix = item.get("suggested_fix", "")

        cat_label = category_labels.get(item_category, item_category)
        cat_color = category_colors.get(item_category, _COLORS["text"])

        card_data = []

        # Category + Title header
        card_data.append([
            Paragraph(
                f'<font color="{cat_color}"><b>[{_sanitize_html(cat_label)}]</b></font> '
                f'<font color="{_COLORS["text"]}"><b>{_sanitize_html(item_title)}</b></font>',
                S["body_small"],
            )
        ])

        # Original text quote
        if item_original_text:
            card_data.append([
                Paragraph(
                    f'<font color="{_COLORS["text_muted"]}">原文：</font>'
                    f'<font color="{_COLORS["text"]}"><i>{_sanitize_html(item_original_text)}</i></font>',
                    S["body_small"],
                )
            ])

        # Critique
        if item_critique:
            card_data.append([
                Paragraph(
                    f'<font color="{_COLORS["text_muted"]}"><b>风险分析：</b></font>'
                    f'<font color="{_COLORS["text"]}">{_sanitize_html(item_critique)}</font>',
                    S["body_small"],
                )
            ])

        # Financial consequence
        if item_financial_consequence:
            card_data.append([
                Paragraph(
                    f'<font color="{_COLORS["critical"]}"><b>财务影响：{_sanitize_html(item_financial_consequence)}</b></font>',
                    S["body_small"],
                )
            ])

        # Suggested fix
        if item_suggested_fix:
            card_data.append([
                Paragraph(
                    f'<font color="{_COLORS["accent"]}"><b>✓ 建议：</b></font>'
                    f'<font color="{_COLORS["text"]}">{_sanitize_html(item_suggested_fix)}</font>',
                    S["body_small"],
                )
            ])

        card = Table(card_data, colWidths=[165 * mm])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(_COLORS["bg_light"])),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(_COLORS["border"])),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(card)
        story.append(Spacer(1, 2 * mm))

    return story


def _build_extra_prediction_section(story: list, prediction: dict, S: dict) -> list:
    """Build a section for extra item prediction in the PDF.

    The `prediction` dict has the structure from ExtraItemPrediction:
    {quoted_total, predicted_actual_total, confidence_range, risk_level, predicted_items}
    """
    quoted_total = prediction.get("quoted_total", 0)
    predicted_total = prediction.get("predicted_actual_total", 0)
    confidence_range = prediction.get("confidence_range", [0, 0])
    risk_level = prediction.get("risk_level", "medium")
    predicted_items = prediction.get("predicted_items", []) or []

    # Risk level colors
    risk_colors = {
        "high": _COLORS["critical"],
        "medium": _COLORS["medium"],
        "low": _COLORS["low"],
    }
    risk_labels = {"high": "高风险", "medium": "中风险", "low": "低风险"}
    risk_color = risk_colors.get(risk_level, _COLORS["text_muted"])
    risk_label = risk_labels.get(risk_level, risk_level)

    # Summary header
    increase = predicted_total - quoted_total
    increase_pct = (increase / quoted_total * 100) if quoted_total > 0 else 0
    summary_text = (
        f'报价单表面总价：<b>{_sanitize_html(f"{quoted_total:,.0f}")} 元</b> | '
        f'预测实际总花费：<b><font color="{risk_color}">{_sanitize_html(f"{predicted_total:,.0f}")} 元</font></b> | '
        f'预估增加：<b><font color="{risk_color}">+{_sanitize_html(f"{increase:,.0f}")} 元 ({increase_pct:.0f}%)</font></b> | '
        f'置信区间：{_sanitize_html(f"{confidence_range[0]:,.0f}")} ~ {_sanitize_html(f"{confidence_range[1]:,.0f}")} 元'
    )
    story.append(Paragraph(summary_text, S["body"]))
    story.append(Spacer(1, 2 * mm))

    # Risk level badge
    story.append(Paragraph(
        f'<font color="{risk_color}"><b>总体风险等级：{risk_label}</b></font>',
        S["body_small"],
    ))
    story.append(Spacer(1, 4 * mm))

    if not predicted_items:
        story.append(Paragraph(
            f'<font color="{_COLORS["text_muted"]}">未检测到明显的增项风险项</font>',
            S["body_small"],
        ))
        return story

    # Predicted items list
    story.append(Paragraph(
        f'预测增项共 <b>{len(predicted_items)}</b> 项，按发生概率从高到低排列：',
        S["body_small"],
    ))
    story.append(Spacer(1, 2 * mm))

    # Probability color mapping
    prob_colors = {
        "极高": _COLORS["critical"],
        "高": _COLORS["high"],
        "中": _COLORS["medium"],
        "低": _COLORS["low"],
    }

    for item in predicted_items:
        name = item.get("name", "")
        probability = item.get("probability", "")
        estimated_amount = item.get("estimated_amount", [0, 0])
        trigger_phase = item.get("trigger_phase", "")
        reason = item.get("reason", "")
        prevention = item.get("prevention", "")

        # Determine color based on probability text
        prob_color = _COLORS["text"]
        for keyword, color in prob_colors.items():
            if keyword in probability:
                prob_color = color
                break

        card_data = []

        # Title row
        card_data.append([
            Paragraph(
                f'<font color="{_COLORS["text"]}"><b>{_sanitize_html(name)}</b></font>',
                S["body_small"],
            )
        ])

        # Meta row: probability + amount + phase
        meta_parts = [
            f'<font color="{prob_color}"><b>概率：{_sanitize_html(probability)}</b></font>',
            f'<font color="{_COLORS["text"]}">预估金额：{_sanitize_html(f"{estimated_amount[0]:,.0f}")} ~ {_sanitize_html(f"{estimated_amount[1]:,.0f}")} 元</font>',
        ]
        if trigger_phase:
            meta_parts.append(
                f'<font color="{_COLORS["text_muted"]}">触发阶段：{_sanitize_html(trigger_phase)}</font>'
            )
        card_data.append([
            Paragraph(" | ".join(meta_parts), S["body_small"])
        ])

        # Reason
        if reason:
            card_data.append([
                Paragraph(
                    f'<font color="{_COLORS["text_muted"]}"><b>预测理由：</b></font>'
                    f'<font color="{_COLORS["text"]}">{_sanitize_html(reason)}</font>',
                    S["body_small"],
                )
            ])

        # Prevention
        if prevention:
            card_data.append([
                Paragraph(
                    f'<font color="{_COLORS["accent"]}"><b>✓ 预防建议：</b></font>'
                    f'<font color="{_COLORS["text"]}">{_sanitize_html(prevention)}</font>',
                    S["body_small"],
                )
            ])

        card = Table(card_data, colWidths=[165 * mm])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(_COLORS["bg_light"])),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(prob_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(_COLORS["border"])),
        ]))
        story.append(card)
        story.append(Spacer(1, 2 * mm))

    return story


def _sanitize_html(text: str) -> str:
    """Escape HTML special characters to prevent ReportLab XML parsing errors."""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("&", "&")
    text = text.replace("<", "<")
    text = text.replace(">", ">")
    text = text.replace('"', '"')
    text = text.replace("'", "&#39;")
    return text


# ── Page Templates ─────────────────────────────────────────────────
_COVER_FRAME = Frame(25 * mm, 25 * mm, 170 * mm, 257 * mm, id="cover")
_CONTENT_FRAME = Frame(25 * mm, 30 * mm, 170 * mm, 242 * mm, id="content")


def _cover_tmpl(canvas, doc):
    canvas.saveState()
    # Accent bar on left
    canvas.setFillColor(colors.HexColor(_COLORS["accent"]))
    canvas.rect(0, 0, 6 * mm, A4[1], fill=1, stroke=0)
    # Subtle footer
    _ensure_font_registered()
    cover_font = _CN_FONT if _CN_FONT in pdfmetrics._fonts else "Helvetica"
    canvas.setFont(cover_font, 8)
    canvas.setFillColor(colors.HexColor(_COLORS["text_muted"]))
    canvas.drawCentredString(A4[0] / 2, 15 * mm, "Renovation Pitfall Analyzer — AI 驱动的装修避坑工具")
    canvas.restoreState()


def _content_tmpl(canvas, doc):
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(colors.HexColor(_COLORS["accent"]))
    canvas.setLineWidth(0.5)
    canvas.line(25 * mm, A4[1] - 20 * mm, A4[0] - 25 * mm, A4[1] - 20 * mm)
    # Page number
    _ensure_font_registered()
    content_font = _CN_FONT if _CN_FONT in pdfmetrics._fonts else "Helvetica"
    canvas.setFont(content_font, 8)
    canvas.setFillColor(colors.HexColor(_COLORS["text_muted"]))
    canvas.drawCentredString(A4[0] / 2, 15 * mm, f"- {doc.page} -")
    canvas.restoreState()


# ── Main Generator ─────────────────────────────────────────────────
def generate_pdf(
    project_id: str,
    result_data: dict,
    images_data: list,
    document_analyses_data: Optional[dict] = None,
) -> Optional[bytes]:
    """Generate a PDF report for the given project.

    Accepts pre-computed `result_data` (from the /api/projects/{id}/result endpoint)
    and `images_data` (from DB query), so data processing logic is consistent
    between the web frontend and the PDF.

    Args:
        project_id: The project UUID.
        result_data: The analysis result dict as returned by `_build_result_data()`.
        images_data: List of image info dicts with keys:
            id, original_name, original_filename, storage_path, width, height.
        document_analyses_data: Optional list of DocumentAnalysis dicts for the
            contract / quotation risk analysis section.

    Returns:
        PDF bytes, or None if generation fails.
    """
    try:
        _ensure_font_registered()

        # Build analysis_data dict in the format _build_content() expects
        analysis_data = {
            "id": str(result_data.get("id", "")),
            "created_at": str(result_data.get("created_at", "")),
            "completed_at": str(result_data.get("completed_at", "")),
            "summary": result_data.get("summary", {}),
            "pitfalls": result_data.get("pitfalls", []),
            "result_json": {},
        }

        # Build PDF
        buf = io.BytesIO()
        doc = BaseDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=25 * mm,
            rightMargin=25 * mm,
            topMargin=25 * mm,
            bottomMargin=25 * mm,
            title=f"装修避坑分析报告 - {project_id[:8]}",
            author="Renovation Pitfall Analyzer",
        )

        doc.addPageTemplates([
            PageTemplate(id="Cover", frames=[_COVER_FRAME], onPage=_cover_tmpl),
            PageTemplate(id="Content", frames=[_CONTENT_FRAME], onPage=_content_tmpl),
        ])

        story = _build_content(project_id, analysis_data, images_data, document_analyses_data)
        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()

        logger.info(f"PDF generated for project {project_id}: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.exception(f"PDF generation failed for project {project_id}: {e}")
        return None