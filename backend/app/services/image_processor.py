"""
Image Processor Service — 图像预处理工具
读取图片、检查分辨率、压缩超大图片
"""

import io
import os

from PIL import Image, UnidentifiedImageError

# 最大分辨率限制（宽或高）
MAX_DIMENSION = 2000
# 压缩后保存质量
JPEG_QUALITY = 85


def get_image_dimensions(file_path: str) -> tuple[int, int]:
    """获取图片宽高，不修改文件

    Args:
        file_path: 图片文件路径

    Returns:
        (width, height) 元组
    """
    with Image.open(file_path) as img:
        return img.size


def needs_resize(file_path: str) -> bool:
    """检查图片是否需要压缩（任一边超过 2000px）

    Args:
        file_path: 图片文件路径

    Returns:
        True 需要压缩，False 无需压缩
    """
    w, h = get_image_dimensions(file_path)
    return w > MAX_DIMENSION or h > MAX_DIMENSION


def compress_image(file_path: str) -> str:
    """等比压缩图片，保留 EXIF 方向，返回压缩后路径（原地修改）

    Args:
        file_path: 原图文件路径

    Returns:
        压缩后的文件路径（与原图相同，原地覆盖）

    Raises:
        UnidentifiedImageError: 无法识别的图像格式
    """
    with Image.open(file_path) as img:
        # 保留 EXIF 信息以正确处理旋转
        exif = img.info.get("exif")

        w, h = img.size
        if w <= MAX_DIMENSION and h <= MAX_DIMENSION:
            return file_path  # 无需压缩

        # 等比缩放
        ratio = min(MAX_DIMENSION / w, MAX_DIMENSION / h)
        new_size = (int(w * ratio), int(h * ratio))

        # 使用高质量 LANCZOS 重采样
        img_resized = img.resize(new_size, Image.LANCZOS)

        # 转为 RGB 模式（兼容 PNG RGBA）
        if img_resized.mode in ("RGBA", "P"):
            img_resized = img_resized.convert("RGB")

        # 保存为 JPEG（覆盖原文件）
        save_kwargs = {"quality": JPEG_QUALITY, "optimize": True}
        if exif:
            save_kwargs["exif"] = exif

        img_resized.save(file_path, "JPEG", **save_kwargs)

    return file_path


def get_image_bytes(file_path: str) -> bytes:
    """读取图片文件的二进制内容

    Args:
        file_path: 图片文件路径

    Returns:
        图片二进制数据
    """
    with open(file_path, "rb") as f:
        return f.read()


def image_to_base64(file_path: str) -> str:
    """将图片文件转为 Base64 编码字符串（用于 AI API 调用）

    Args:
        file_path: 图片文件路径

    Returns:
        Base64 编码的图片数据
    """
    import base64

    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")