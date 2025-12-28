from __future__ import annotations

from pathlib import Path
from typing import List, Dict
from dataclasses import asdict
import time

from triclick_doc_toolset.framework import Command, Context, CommandRegistry
from triclick_doc_toolset.common.rtf import split_rtf_into_tables_with_copy
from triclick_doc_toolset.common import TableItem

class RtfFilePartitionCommand(Command):
    """RTF 拆分命令

    消费 `Context.sections` 中的解析结果，基于索引拼接生成独立 `.rtf` 文件：
    - 按 `source_file` 分组处理；
    - 写回 `local_path` 与处理摘要；
    - 与 DOCX 拆分命令对齐语义，便于流水线复用。
    """

    def is_satisfied(self, context: Context) -> bool:
        return context.has_document()

    def _to_table_item(self, d: Dict) -> TableItem:
        """将结构化字典转换为 `TableItem`，过滤 None 并保持类型安全"""
        ti = TableItem(
            level=int(d.get("level", 0) or 0),
            table_index=d.get("table_index"),
            label=d.get("label"),
            section=d.get("section"),
            title=d.get("title"),
        )
        ti.title_indices = [int(i) for i in (d.get("title_indices") or []) if isinstance(i, int)]
        ti.footnote = d.get("footnote")
        ti.footnote_indices = [int(i) for i in (d.get("footnote_indices") or []) if isinstance(i, int)]
        ti.local_path = d.get("local_path")
        return ti

    def execute(self, context: Context) -> Context:
        sections_in = context.sections or []
        if not sections_in:
            context.add_error("No parsed sections found in context; run partition first")
            return context

        grouped: Dict[str, List[TableItem]] = {}
        for d in sections_in:
            src = d.get("source_file")
            if not src:
                continue
            grouped.setdefault(src, []).append(self._to_table_item(d))

        out_dirs: List[str] = []
        generated_files: List[str] = []
        sections_out: List[dict] = []

        for src_str, items in grouped.items():
            _start = time.perf_counter()
            src = Path(src_str)
            base_out = context.metadata.get("output_dir")
            if not base_out:
                context.add_error("RtfFilePartitionCommand requires context.metadata['output_dir']")
                return context
            out_dir_str = str(base_out)

            updated_items = split_rtf_into_tables_with_copy(str(src), items, output_dir=out_dir_str)
            out_dirs.append(out_dir_str)

            for sec in updated_items:
                d = asdict(sec)
                d["source_file"] = src_str
                sections_out.append(d)
                if d.get("local_path"):
                    generated_files.append(d["local_path"]) 

            _elapsed = time.perf_counter() - _start
            context.processing_summary.setdefault("rtf_split", []).append({"file": src_str, "elapsed": _elapsed})

        context.doc_type = "rtf"
        context.sections = sections_out
        tables_processed = sum(1 for d in sections_out if (d.get("local_path") and (d.get("type") or "table").strip().lower() == "table"))
        context.processing_summary["title_table_footnote_split_rtf"] = {
            "files_processed": len(grouped),
            "tables_processed": tables_processed,
            "generated_files_count": len(generated_files),
            "output_dirs": out_dirs,
            "mode": "copy_elements",
        }
        context.generated_files.extend(generated_files)
        return context

CommandRegistry.register("RtfFilePartitionCommand", RtfFilePartitionCommand)
