"""
PDF 报告生成服务
基于分析结果 JSON 渲染排版精致的 PDF 报告
"""

import io
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.project import Project
from ..models.analysis import Analysis

logger = logging.getLogger(__name__)

# 延迟导入 reportlab，避免启动时加载失败
_REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    _REPORTLAB_AVAILABLE = True
except ImportError:
    pass

# 颜色常量（纯字符串，无 reportlab 依赖）
_HEX_COLORS = {
    "primary": "#1a237e",
    "accent": "#0d47a1",
    "success": "#2e7d32",
    "warning": "#e65100",
    "danger": "#c62828",
    "info": "#01579b",
    "muted": "#757575",
    "light_bg": "#f5f5f5",
    "white": "#ffffff",
    "border": "#e0e0e0",
}

_HEX_SEVERITY = {
    "critical": "#c62828",
    "high": "#e65100",
    "medium": "#f9a825",
    "low": "#2e7d32",
    "info": "#01579b",
}

SEVERITY_LABELS = {
    "critical": "严重",
    "high": "高",
    "medium": "中",
    "low": "低",
    "info": "提示",
}


def _get_colors() -> dict:
    """延迟创建 HexColor 对象（仅在 reportlab 可用时调用）"""
    from reportlab.lib.colors import HexColor
    return {k: HexColor(v) for k, v in _HEX_COLORS.items()}


def _get_severity_colors() -> dict:
    """延迟创建严重程度颜色映射"""
    from reportlab.lib.colors import HexColor
    return {k: HexColor(v) for k, v in _HEX_SEVERITY.items()}


def _register_fonts():
    """注册中文字体"""
    try:
        # macOS 系统字体
        pdfmetrics.registerFont(TTFont("SimSun", "/System/Library/Fonts/STHeiti Light.ttc"))
        pdfmetrics.registerFont(TTFont("SimHei", "/System/Library/Fonts/STHeiti Medium.ttc"))
        return "SimHei"
    except Exception:
        try:
            pdfmetrics.registerFont(TTFont("SimSun", "/System/Library/Fonts/PingFang.ttc"))
            return "SimSun"
        except Exception:
            logger.warning("无法注册中文字体，PDF 中文可能无法正常显示")
            return "Helvetica"


def _build_styles(font_name: str) -> dict:
    """构建段落样式"""
    from reportlab.lib.colors import HexColor

    colors = _get_colors()
    styles = {}

    styles["title"] = ParagraphStyle(
        "ReportTitle",
        fontName=font_name,
        fontSize=22,
        leading=28,
        textColor=colors["primary"],
        spaceAfter=6 * mm,
        alignment=TA_CENTER,
    )

    styles["subtitle"] = ParagraphStyle(
        "ReportSubtitle",
        fontName=font_name,
        fontSize=12,
        leading=16,
        textColor=colors["muted"],
        spaceAfter=10 * mm,
        alignment=TA_CENTER,
    )

    styles["h1"] = ParagraphStyle(
        "H1",
        fontName=font_name,
        fontSize=16,
        leading=22,
        textColor=colors["primary"],
        spaceBefore=8 * mm,
        spaceAfter=4 * mm,
        borderPadding=(0, 0, 2, 0),
    )

    styles["h2"] = ParagraphStyle(
        "H2",
        fontName=font_name,
        fontSize=13,
        leading=18,
        textColor=colors["accent"],
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )

    styles["body"] = ParagraphStyle(
        "Body",
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=HexColor("#333333"),
        spaceAfter=2 * mm,
        alignment=TA_JUSTIFY,
    )

    styles["body_small"] = ParagraphStyle(
        "BodySmall",
        fontName=font_name,
        fontSize=8,
        leading=11,
        textColor=colors["muted"],
    )

    styles["problem_title"] = ParagraphStyle(
        "ProblemTitle",
        fontName=font_name,
        fontSize=12,
        leading=17,
        textColor=colors["primary"],
        spaceBefore=3 * mm,
        spaceAfter=1 * mm,
    )

    styles["label"] = ParagraphStyle(
        "Label",
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors["muted"],
        spaceAfter=1 * mm,
    )

    styles["bullet"] = ParagraphStyle(
        "Bullet",
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=HexColor("#333333"),
        leftIndent=8 * mm,
        spaceAfter=1 * mm,
    )

    return styles


def _build_summary_table(summary: dict, styles: dict, font_name: str) -> Table:
    """构建摘要统计表格"""
    colors = _get_colors()
    severity_colors = _get_severity_colors()

    data = [
        [
            Paragraph("严重程度", styles["label"]),
            Paragraph("数量", styles["label"]),
        ]
    ]

    severity_order = ["critical", "high", "medium", "low", "info"]
    for sev in severity_order:
        count = summary.get("by_severity", {}).get(sev, 0)
        data.append([
            Paragraph(f'<font color="{severity_colors[sev]}">● {SEVERITY_LABELS[sev]}</font>', styles["body"]),
            Paragraph(str(count), styles["body"]),
        ])

    data.append([
        Paragraph('<b>总计</b>', styles["body"]),
        Paragraph(f'<b>{summary.get("total", 0)}</b>', styles["body"]),
    ])

    table = Table(data, colWidths=[60 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors["white"]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors["border"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors["white"], colors["light_bg"]]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    return table


def _build_problem_section(problem: dict, index: int, styles: dict, font_name: str) -> list:
    """构建单个问题的内容"""
    colors = _get_colors()
    severity_colors = _get_severity_colors()

    elements = []

    severity = problem.get("severity", "low")
    severity_label = SEVERITY_LABELS.get(severity, "低")
    category = problem.get("category", "其他")

    # 问题标题（带序号、严重程度标签、分类）
    title_text = (
        f'<font size="10" color="{colors["muted"]}">问题 {index}</font>  '
        f'<font size="14">{problem.get("title", "未命名问题")}</font>  '
        f'<font size="9" color="{severity_colors[severity]}">[{severity_label}]</font>  '
        f'<font size="9" color="{colors["muted"]}">{category}</font>'
    )
    elements.append(Paragraph(title_text, styles["problem_title"]))

    # 描述
    if problem.get("description"):
        elements.append(Paragraph(problem["description"], styles["body"]))

    # 位置信息
    if problem.get("location"):
        elements.append(Paragraph(
            f'<font color="{colors["muted"]}">📍 位置：{problem["location"]}</font>',
            styles["body_small"]
        ))

    # 相关规范
    if problem.get("regulation_ref"):
        elements.append(Paragraph(
            f'<font color="{colors["muted"]}">📋 参考规范：{problem["regulation_ref"]}</font>',
            styles["body_small"]
        ))

    # 建议方案
    if problem.get("suggestion"):
        elements.append(Paragraph(
            f'<font color="{colors["success"]}">💡 建议方案：{problem["suggestion"]}</font>',
            styles["body"]
        ))

    # 预估损失（如有）
    if problem.get("estimated_loss"):
        elements.append(Paragraph(
            f'<font color="{colors["danger"]}">⚠️ 潜在损失：{problem["estimated_loss"]}</font>',
            styles["body_small"]
        ))

    elements.append(Spacer(1, 3 * mm))

    return elements


def generate_pdf(project_id: str) -> Optional[bytes]:
    """
    生成 PDF 报告

    Args:
        project_id: 项目 ID

    Returns:
        PDF 文件字节流，或 None（如果报告不可用）
    """
    if not _REPORTLAB_AVAILABLE:
        logger.error("reportlab 未安装，无法生成 PDF")
        return None

    db: Session = SessionLocal()
    try:
        # 加载项目
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project not found: {project_id}")
            return None

        # 加载最新完成的 Analysis
        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.project_id == project_id,
                Analysis.status == "completed",
            )
            .order_by(Analysis.completed_at.desc())
            .first()
        )

        if not analysis or not analysis.raw_result_json:
            logger.error(f"No completed analysis for project={project_id}")
            return None

        result_data = analysis.raw_result_json
        problems = result_data.get("problems", [])
        summary = result_data.get("summary", {"total": len(problems)})

        # 注册字体
        font_name = _register_fonts()
        styles = _build_styles(font_name)

        # 创建 PDF 缓冲区
        buffer = io.BytesIO()

        # 构建文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=f"装修避坑分析报告 - {project_id[:8]}",
            author="RenovationPitfallAnalyzer",
        )

        story = []

        colors = _get_colors()

        # ===== 封面 =====
        story.append(Spacer(1, 30 * mm))
        story.append(Paragraph("装修设计避坑分析报告", styles["title"]))
        story.append(Paragraph(
            f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            styles["subtitle"]
        ))

        # ===== 项目信息 =====
        story.append(HRFlowable(
            width="100%", thickness=1, color=colors["border"],
            spaceBefore=5 * mm, spaceAfter=5 * mm,
        ))
        story.append(Paragraph("项目信息", styles["h1"]))
        info_data = [
            [Paragraph("项目 ID", styles["label"]), Paragraph(project.id[:8], styles["body"])],
            [Paragraph("创建时间", styles["label"]), Paragraph(project.created_at.strftime("%Y-%m-%d %H:%M"), styles["body"])],
            [Paragraph("分析完成时间", styles["label"]), Paragraph(
                analysis.completed_at.strftime("%Y-%m-%d %H:%M") if analysis.completed_at else "-",
                styles["body"]
            )],
            [Paragraph("用户补充说明", styles["label"]), Paragraph(project.input_text or "无", styles["body"])],
        ]
        info_table = Table(info_data, colWidths=[35 * mm, 120 * mm])
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors["light_bg"]),
        ]))
        story.append(info_table)

        # ===== 摘要 =====
        story.append(PageBreak())
        story.append(Paragraph("分析摘要", styles["h1"]))
        story.append(Paragraph(
            f"本次分析共发现 <b>{summary.get('total', len(problems))} 个</b>潜在问题，"
            f"涵盖 {len(set(p.get('category', '') for p in problems))} 个类别。",
            styles["body"]
        ))

        # 总体结论
        if summary.get("overall_assessment"):
            story.append(Paragraph(summary["overall_assessment"], styles["body"]))

        story.append(Spacer(1, 5 * mm))
        story.append(_build_summary_table(summary, styles, font_name))

        # ===== 问题详情 =====
        story.append(PageBreak())
        story.append(Paragraph("问题详情", styles["h1"]))

        if problems:
            story.append(Paragraph(f"共列出 {len(problems)} 个问题：", styles["body"]))
            story.append(Spacer(1, 3 * mm))

            for i, problem in enumerate(problems, 1):
                elements = _build_problem_section(problem, i, styles, font_name)
                story.extend(elements)

                # 问题之间分割线
                if i < len(problems):
                    story.append(HRFlowable(
                        width="100%", thickness=0.5, color=colors["light_bg"],
                    ))
        else:
            story.append(Paragraph("未发现明显问题。", styles["body"]))

        # ===== 免责声明 =====
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(
            width="100%", thickness=1, color=colors["border"],
        ))
        story.append(Paragraph("免责声明", styles["h2"]))
        story.append(Paragraph(
            "本报告由 AI 系统自动生成，分析结果仅供参考。实际装修施工前，"
            "请咨询具有资质的专业设计师和施工团队。报告中的建议不构成法律或合同义务。",
            styles["body_small"]
        ))

        # 生成 PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"PDF generated for project={project_id}, {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.exception(f"PDF generation failed: {e}")
        return None

    finally:
        db.close()