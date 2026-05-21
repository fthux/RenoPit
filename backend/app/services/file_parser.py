"""
File Parser Service — 文本文件内容提取器
支持 .txt / .md / .docx / .pdf 格式的纯文本提取
"""

from docx import Document
import fitz  # PyMuPDF


def extract_text_from_txt(file_path: str) -> str:
    """从 .txt 文件读取纯文本内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_from_md(file_path: str) -> str:
    """从 .md 文件读取原始内容（保留 Markdown 标记供 AI 分析）"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_from_docx(file_path: str) -> str:
    """从 .docx 文件提取纯文本"""
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_pdf(file_path: str) -> str:
    """从 .pdf 文件提取纯文本（PyMuPDF）"""
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                text_parts.append(text.strip())
    return "\n\n".join(text_parts)


def extract_text(file_path: str, file_type: str) -> str:
    """根据文件类型提取纯文本内容

    Args:
        file_path: 文件路径
        file_type: 文件类型（txt / md / docx / pdf）

    Returns:
        提取的纯文本字符串

    Raises:
        ValueError: 不支持的文件类型
    """
    extractors = {
        "txt": extract_text_from_txt,
        "md": extract_text_from_md,
        "docx": extract_text_from_docx,
        "pdf": extract_text_from_pdf,
    }

    if file_type not in extractors:
        raise ValueError(f"不支持的文件类型: {file_type}，支持的类型: txt, md, docx, pdf")

    return extractors[file_type](file_path)