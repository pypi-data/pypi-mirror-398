"""Word 文档处理子包导出：统一暴露常用工具函数。"""

from .docx_file_parse_util import (
    extract_docx_content_with_metadata,
    extract_title_label,
)
from .docx_file_partition_util import (
    split_docx_into_tables_with_copy,
)
from .title_util import (
    assemble_title_lines,
    normalize_docx_text,
    extract_leading_enumerator,
    get_paragraph_font_info,
    is_structure_separator,
)

__all__ = [
    "extract_docx_content_with_metadata",
    "extract_title_label",
    "split_docx_into_tables_with_copy",
    "assemble_title_lines",
    "normalize_docx_text",
    "extract_leading_enumerator",
    "get_paragraph_font_info",
    "is_structure_separator",
]