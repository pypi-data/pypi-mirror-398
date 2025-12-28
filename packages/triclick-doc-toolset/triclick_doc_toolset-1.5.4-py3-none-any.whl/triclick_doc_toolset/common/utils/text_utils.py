"""
通用文本处理工具函数
"""
import re


def slugify_text(text: str) -> str:
    """
    将文本转换为安全文件名片段：空白转下划线，移除非字母数字/点/横线字符，并折叠连续下划线。

    参数:
    - text: 原始标签文本。

    返回: 规范化后的短标签字符串。
    """
    s = re.sub(r"\s+", "_", (text or "").strip())
    s = re.sub(r"[^\w\.\-]", "", s)
    return re.sub(r"_+", "_", s)