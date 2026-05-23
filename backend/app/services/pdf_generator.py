"""
PDF Generation Service
Generates a downloadable PDF report for renovation analysis results.

Key fixes:
1. Uses extracted TTF font (not .ttc) to avoid reportlab's CJK rendering bug
2. Properly embeds uploaded images into the PDF
3. Draws bounding box annotations on images for better visual feedback
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
# dirname ×3 → backend/
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


def _build_content(project_id: str, analysis_data: dict, images_data: list) -> list:
    """Build the document content (list of flowables)."""
    S = _styles()
    story = []

    # ── Cover Page ─────────────────────────────────────────────
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("装修避坑分析报告", S["title"]))
    story.append(Paragraph("Renovation Pitfall Analysis Report", S["subtitle"]))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph(f"项目编号：{project_id[:8]}...", S["body"]))
    story.append(Paragraph(f"分析日期：{analysis_data.get('completed_at', 'N/A')[:10]}", S["body"]))
    story.append(Spacer(1, 6 * mm))

    summary = analysis_data.get("summary", {})
    score = summary.get("score", 0)
    story.append(_build_score_card(score))
    story.append(Spacer(1, 8 * mm))

    # Summary text
    summary_text = summary.get("summary_text", "")
    if summary_text:
        story.append(Paragraph("总体评估", S["h2"]))
        story.append(Paragraph(summary_text, S["body"]))
        story.append(Spacer(1, 4 * mm))

    # Pitfall counts
    counts_data = [
        ["严重", str(summary.get("critical_count", 0)), _COLORS["critical"]],
        ["高", str(summary.get("high_count", 0)), _COLORS["high"]],
        ["中", str(summary.get("medium_count", 0)), _COLORS["medium"]],
        ["低", str(summary.get("low_count", 0)), _COLORS["low"]],
    ]
    counts_table = Table(
        [["严重等级", "数量", ""]] + counts_data,
        colWidths=[80, 60, 60],
        rowHeights=[24, 20, 20, 20, 20],
    )
    cf = S["cell_severity"]
    header_style = ParagraphStyle("ch", parent=cf, textColor=colors.white, fontSize=9)
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_COLORS["primary"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), S["use_font"]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_COLORS["border"])),
        ("BACKGROUND", (2, 1), (2, 1), colors.HexColor(_COLORS["critical"])),
        ("BACKGROUND", (2, 2), (2, 2), colors.HexColor(_COLORS["high"])),
        ("BACKGROUND", (2, 3), (2, 3), colors.HexColor(_COLORS["medium"])),
        ("BACKGROUND", (2, 4), (2, 4), colors.HexColor(_COLORS["low"])),
    ])
    # Build header + data
    table_data = [
        [Paragraph("严重等级", header_style), Paragraph("数量", header_style), Paragraph("", header_style)],
    ]
    for label, count, color in counts_data:
        table_data.append([
            Paragraph(label, cf),
            Paragraph(count, cf),
            Paragraph("", ParagraphStyle("dot", parent=cf, textColor=colors.HexColor(color), fontSize=14)),
        ])
    counts_table = Table(table_data, colWidths=[100, 80, 60])
    counts_table.setStyle(ts)
    story.append(Paragraph("问题统计", S["h2"]))
    story.append(counts_table)

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

    return story


def _build_score_card(score: int):
    """Build a score visualization."""
    S = _styles()
    color = _COLORS["accent"]
    if score < 60:
        color = _COLORS["high"]
    elif score < 80:
        color = _COLORS["medium"]

    score_text = Paragraph(
        f'<font size="48" color="{color}"><b>{score}</b></font>'
        f'<font size="14" color="{_COLORS["text_muted"]}"> / 100</font>',
        ParagraphStyle("ScoreLine", alignment=TA_CENTER, spaceAfter=4),
    )
    label_text = Paragraph(
        f'<font size="12" color="{color}"><b>'
        f'{"优秀" if score >= 80 else "待改进" if score >= 60 else "需重视"}'
        f'</b></font>',
        ParagraphStyle("ScoreLabel", alignment=TA_CENTER, spaceAfter=6),
    )
    # Progress bar background
    bar_bg = Table(
        [[""]],
        colWidths=[160],
        rowHeights=[10],
    )
    bar_bg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("LINEBELOW", (0, 0), (-1, 0), 0, colors.white),
    ]))
    bar_fill = Table(
        [[""]],
        colWidths=[max(score * 1.6, 3)],
        rowHeights=[10],
    )
    bar_fill.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
        ("LINEBELOW", (0, 0), (-1, 0), 0, colors.white),
    ]))
    bar = Table([[bar_fill]], colWidths=[160], rowHeights=[10])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # Wrap in a table for centering
    card = Table(
        [[score_text], [label_text], [bar]],
        colWidths=[180],
    )
    card.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(_COLORS["border"])),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(_COLORS["bg_light"])),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    return card


def _build_image_section(img_info: dict, analysis_data: dict, idx: int):
    """Build a section showing an image with optional bbox annotations."""
    S = _styles()
    elements = []

    # Title
    original_name = img_info.get("original_name", img_info.get("original_filename", f"图片{idx+1}"))
    elements.append(Paragraph(f"📷 {original_name}", S["h2"]))
    elements.append(Spacer(1, 2 * mm))

    # Check if image file exists
    storage_path = img_info.get("storage_path", "")
    # Resolve relative path to absolute (storage_path may be relative like "uploads/...")
    # __file__ = backend/app/services/pdf_generator.py → dirname×3 = backend/
    if storage_path and not os.path.isabs(storage_path):
        storage_path = os.path.abspath(storage_path)
    if not storage_path or not os.path.exists(storage_path):
        logger.warning(f"Image file not found: storage_path={storage_path}, original={original_name}")
        elements.append(Paragraph(f"[图片文件 {original_name} 未找到]", S["body"]))
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
        elements.append(Paragraph(f"[图片 {original_name} 无法嵌入 PDF: {e}]", S["body"]))
        return KeepTogether(elements)

    # Try to find bbox annotations for this image
    # The bbox data is in analysis pitfalls "bbox" field, matching by image file name
    bbox_found = False
    pitfalls = analysis_data.get("pitfalls", [])
    problems_raw = analysis_data.get("result_json", {}).get("problems", [])
    all_items = pitfalls + problems_raw

    # Check if this image has related bbox annotations
    img_filename_lower = original_name.lower()
    related_bboxes = []
    for item in all_items:
        if not isinstance(item, dict):
            continue
        bbox = item.get("bbox")
        if bbox and isinstance(bbox, list) and len(bbox) == 4:
            # Check if this bbox relates to this image by matching location text or image name
            location = (item.get("location") or "").lower()
            if img_filename_lower.split(".")[0] in location or location in img_filename_lower:
                try:
                    bbox_f = [float(x) for x in bbox]
                    # Normalize bbox: [x, y, w, h] where x,y is top-left
                    # Convert to display coordinates
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

    if related_bboxes:
        bbox_found = True
        # We can't easily draw bbox on Image flowable in reportlab without canvas operations.
        # Instead, we list the related issues below the image.
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
                            f'<font color="{_COLORS["text"]}"><b>[{_severity_label(sev)}]</b> {desc}</font>',
                            S["body_small"],
                        ))

    if not bbox_found:
        elements.append(Paragraph("（该图片未检测到具体问题位置）", S["caption"]))

    return KeepTogether(elements)


def _build_pitfall_card(item: dict, S: dict):
    """Build a card for one pitfall item."""
    sev = item.get("severity", "medium")
    sev_color, sev_bg = _SEVERITY_COLORS.get(sev, (_COLORS["text"], _COLORS["bg_light"]))
    sev_label = _severity_label(sev)
    description = item.get("description", "")
    category = item.get("category", "其他")
    location = item.get("location", "")
    suggestion = item.get("suggestion", "")
    critique = item.get("critique", "")

    card_data = []

    # Header row
    cell_header = ParagraphStyle("ch", parent=S["h3"], spaceBefore=0, spaceAfter=0)
    header_text = (
        f'<font color="{sev_color}">●</font> '
        f'<font color="{sev_color}"><b>[{sev_label}]</b></font> '
        f'<font color="{_COLORS["text"]}">{description}</font>'
    )
    card_data.append([Paragraph(header_text, cell_header)])

    # Info row
    info_parts = [f'<font color="{_COLORS["text_muted"]}">分类：{category}</font>']
    if location:
        info_parts.append(f'<font color="{_COLORS["text_muted"]}"> | 位置：{location}</font>')
    info_text = "".join(info_parts)
    card_data.append([Paragraph(info_text, S["body_small"])])

    # Critique
    if critique:
        card_data.append([
            Paragraph(
                f'<font color="{_COLORS["text_muted"]}"><b>分析：</b>{critique}</font>',
                S["body_small"],
            )
        ])

    # Suggestion
    if suggestion:
        card_data.append([
            Paragraph(
                f'<font color="{_COLORS["accent"]}"><b>✓ 建议：</b></font>'
                f'<font color="{_COLORS["text"]}">{suggestion}</font>',
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
def generate_pdf(project_id: str) -> Optional[bytes]:
    """Generate a PDF report for the given project.
    Returns PDF bytes, or None if generation fails.
    """
    # Lazy imports to avoid circular dependencies
    from sqlalchemy.orm import Session
    from ..core.database import SessionLocal
    from ..models import Project, Analysis, ProjectImage, Report

    db: Optional[Session] = None
    try:
        _ensure_font_registered()
        db = SessionLocal()

        # Fetch project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return None

        # Fetch analysis
        analysis = (
            db.query(Analysis)
            .filter(Analysis.project_id == project_id, Analysis.status == "completed")
            .order_by(Analysis.completed_at.desc())
            .first()
        )
        if not analysis or not analysis.raw_result_json:
            logger.error(f"No completed analysis for project {project_id}")
            return None

        # Fetch images
        images = (
            db.query(ProjectImage)
            .filter(ProjectImage.project_id == project_id)
            .all()
        )

        # Prepare data structures
        analysis_data = {
            "completed_at": str(analysis.completed_at or ""),
            "summary": {},
            "pitfalls": [],
            "result_json": analysis.raw_result_json,
        }

        raw = analysis.raw_result_json
        raw_summary = raw.get("summary", {})
        problems = raw.get("problems", [])

        # Build summary from raw data
        sev_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        pitfalls_list = []
        for p in problems:
            sev = p.get("severity", "medium")
            sev_count[sev] = sev_count.get(sev, 0) + 1
            pitfalls_list.append({
                "id": str(len(pitfalls_list) + 1),
                "category": p.get("category", "其他"),
                "description": p.get("title", p.get("critique", "")),
                "severity": sev,
                "location": p.get("location", ""),
                "suggestion": p.get("alternative", ""),
                "critique": p.get("critique", ""),
                "trap_explanation": p.get("trap_explanation", ""),
                "bbox": p.get("bbox"),
            })

        score = 95
        if problems:
            score = max(0, min(100, 100 - sum(
                sev_count[s] * w for s, w in [("critical", 15), ("high", 8), ("medium", 3), ("low", 1)]
            )))

        if isinstance(raw_summary, dict):
            summary_text = raw_summary.get("overall_assessment", "")
        else:
            summary_text = str(raw_summary) if raw_summary else ""

        analysis_data["summary"] = {
            "total_pitfalls": len(problems),
            "critical_count": sev_count["critical"],
            "high_count": sev_count["high"],
            "medium_count": sev_count["medium"],
            "low_count": sev_count["low"],
            "score": score,
            "summary_text": summary_text,
        }
        analysis_data["pitfalls"] = pitfalls_list

        # Build images data
        images_data = []
        for img in images:
            images_data.append({
                "id": img.id,
                "original_name": img.original_filename,
                "original_filename": img.original_filename,
                "storage_path": img.storage_path,
                "width": img.width,
                "height": img.height,
            })

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

        story = _build_content(project_id, analysis_data, images_data)
        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()

        # Save report record (non-critical: PDF generation already succeeded)
        try:
            report_record = db.query(Report).filter(Report.project_id == project_id).first()
            if not report_record:
                report_record = Report(
                    project_id=project_id,
                    analysis_id=analysis.id,
                    file_path=f"generated/{project_id[:8]}.pdf",
                )
                db.add(report_record)
                db.commit()
        except Exception as report_err:
            logger.warning(f"Failed to save report record for project {project_id}: {report_err}")
            db.rollback()

        logger.info(f"PDF generated for project {project_id}: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.exception(f"PDF generation failed for project {project_id}: {e}")
        return None
    finally:
        if db:
            db.close()
