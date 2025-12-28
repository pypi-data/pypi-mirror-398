"""RTF 适配子包导出

提供与 DOCX 等价的解析与拆分工具入口：
- `extract_rtf_content_with_metadata`：解析 RTF 文本，输出标题/表格/脚注的元数据（TableItem）。
- `split_rtf_into_tables_with_copy`：按元数据从原始 RTF 拼接生成独立的表格文件。
"""
from .rtf_file_parse_util import extract_rtf_content_with_metadata
from .rtf_file_partition_util import split_rtf_into_tables_with_copy

__all__ = [
    "extract_rtf_content_with_metadata",
    "split_rtf_into_tables_with_copy",
]
