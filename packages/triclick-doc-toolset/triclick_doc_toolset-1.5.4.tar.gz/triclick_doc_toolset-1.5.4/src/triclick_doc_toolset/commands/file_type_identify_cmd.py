from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

# 框架依赖
from triclick_doc_toolset.framework import Command, Context, CommandRegistry


class FileTypeIdentificationCommand(Command):
    """
    文档类型识别命令：根据输入的文件或文件夹，识别主要文档类型。

    规则：
    - 单文件：按扩展名识别（docx/doc/rtf）。
    - 文件夹：优先选择包含文件数量最多的已支持类型（docx > rtf > doc）。
    - 识别结果写入 `context.doc_type`，并在 processing_summary 中记录统计。
    """

    SUPPORTED_EXTS = {"docx": "docx", "doc": "doc", "rtf": "rtf"}

    def is_satisfied(self, context: Context) -> bool:
        return context.document_uri is not None

    def _count_types(self, paths: List[Path]) -> Dict[str, int]:
        counts: Dict[str, int] = {"docx": 0, "doc": 0, "rtf": 0}
        for p in paths:
            ext = p.suffix.lower().lstrip(".")
            if ext in counts:
                counts[ext] += 1
        return counts

    def execute(self, context: Context) -> Context:
        uri = context.document_uri
        if uri is None:
            context.add_error("No document_uri set in context")
            return context

        # 单文件识别
        if isinstance(uri, (str, Path)) and Path(uri).is_file():
            ext = Path(uri).suffix.lower().lstrip(".")
            doc_type = self.SUPPORTED_EXTS.get(ext, None)
            context.doc_type = doc_type
            context.processing_summary["file_type_identification"] = {
                "source": str(Path(uri)),
                "doc_type": doc_type or "unknown",
            }
            return context

        # 目录或列表识别
        paths = context.resolve_document_paths(patterns=["*.docx", "*.doc", "*.rtf"])
        counts = self._count_types(paths)
        # 选择规则：docx 优先，其次 rtf，再次 doc
        doc_type: Optional[str] = None
        if counts["docx"] > 0:
            doc_type = "docx"
        elif counts["rtf"] > 0:
            doc_type = "rtf"
        elif counts["doc"] > 0:
            doc_type = "doc"
        else:
            doc_type = None
        context.doc_type = doc_type
        context.processing_summary["file_type_identification"] = {
            "counts": counts,
            "doc_type": doc_type or "unknown",
        }
        return context

# 注册到命令注册表
CommandRegistry.register("FileTypeIdentificationCommand", FileTypeIdentificationCommand)