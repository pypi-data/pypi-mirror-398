from __future__ import annotations

from pathlib import Path
from typing import List, Dict
from dataclasses import asdict
import time
import logging

# 框架依赖
from triclick_doc_toolset.framework import Command, Context, CommandRegistry

# 拆分与标题工具
from triclick_doc_toolset.common.word import (
    split_docx_into_tables_with_copy,
    assemble_title_lines,
)
from triclick_doc_toolset.common import TableItem
from triclick_doc_toolset.common.rules import apply_same_as_rule
from triclick_doc_toolset.common.rules.same_as_rule import get_bytes_cache_stats


class DocxFilePartitionCommand(Command):
    """
    基于“标题-表格-脚注”元数据拆分 DOCX，保留原样式。
    只对接 `split_docx_into_tables_with_copy`，从 Context.sections 读取解析结果，
    处理完后覆盖写回 Context.sections。
    输出目录仅从 Context.metadata['output_dir'] 读取。
    """

    def is_satisfied(self, context: Context) -> bool:
        return context.has_document()

    def _assemble_full_title(self, docx_path: str, indices: List[int]) -> str:
        """兜底组装标题：使用统一公共工具按索引拼接标题。"""
        return assemble_title_lines(docx_path, indices)

    def _to_table_item(self, d: Dict, src_doc_path: str) -> TableItem:
        ti = TableItem(
            level=int(d.get("level", 0) or 0),
            table_index=d.get("table_index"),
            label=d.get("label"),
            section=d.get("section"),
            title=d.get("title"),
        )
        # 安全过滤 None
        ti.title_indices = [int(i) for i in (d.get("title_indices") or []) if isinstance(i, int)]
        ti.footnote = d.get("footnote")
        ti.footnote_indices = [int(i) for i in (d.get("footnote_indices") or []) if isinstance(i, int)]
        ti.local_path = d.get("local_path")
        # 兜底：若存在多行索引而 title 仍为单行，则组装完整标题
        if ti.title_indices and ("\n" not in (ti.title or "")) and len(ti.title_indices) > 1:
            full_title = self._assemble_full_title(src_doc_path, ti.title_indices)
            if full_title:
                ti.title = full_title
        return ti

    def execute(self, context: Context) -> Context:
        # 从 Context.sections 读取解析结果
        sections_in = context.sections or []
        if not sections_in:
            context.add_error("No parsed sections found in context; run partition first")
            return context

        # 按 source_file 分组
        grouped: Dict[str, List[TableItem]] = {}
        for d in sections_in:
            src = d.get("source_file")
            if not src:
                # 无来源则跳过
                continue
            grouped.setdefault(src, []).append(self._to_table_item(d, src))

        out_dirs: List[str] = []
        generated_files: List[str] = []
        sections_out: List[dict] = []

        for src_str, items in grouped.items():
            _start = time.perf_counter()
            src = Path(src_str)
            base_out = context.metadata.get("output_dir")
            if not base_out:
                context.add_error("DocxFilePartitionCommand requires context.metadata['output_dir']")
                return context
            out_dir_str = str(base_out)

            updated_items = split_docx_into_tables_with_copy(str(src), items, output_dir=out_dir_str)
            # 规则：Same-as 复制与重命名（通过 self.rules 控制）
            rule = next((r for r in self.rules if (r.get("name") == "same_as" and r.get("enabled") is True)), None)
            if rule:
                updated_items = apply_same_as_rule(updated_items)
            out_dirs.append(out_dir_str)

            # 写入 Context.sections（结构化 dict），附带 source_file
            for sec in updated_items:
                d = asdict(sec)
                d["source_file"] = src_str
                sections_out.append(d)
                if d.get("local_path"):
                    generated_files.append(d["local_path"])
            _elapsed = time.perf_counter() - _start
            stats = get_bytes_cache_stats()
            context.processing_summary.setdefault("same_as_cache_stats", []).append({"file": src_str, **stats})
            logging.getLogger(__name__).info(f"[{self.name}] 文件处理 {src_str} 耗时 {_elapsed:.2f}s")

        context.doc_type = "docx"
        # 覆盖写回拆分后的分段到 Context
        context.sections = sections_out
        # 记录输出摘要
        tables_processed = sum(1 for d in sections_out if (d.get("local_path") and (d.get("type") or "table").strip().lower() == "table"))
        context.processing_summary["title_table_footnote_split"] = {
            "files_processed": len(grouped),
            "tables_processed": tables_processed,
            "generated_files_count": len(generated_files),
            "output_dirs": out_dirs,
            "mode": "copy_elements",
        }
        # 附加生成文件（可用于后续输出或验证）
        context.generated_files.extend(generated_files)
        return context


# 注册到命令注册表，便于 Pipeline 通过 YAML 创建
CommandRegistry.register("DocxFilePartitionCommand", DocxFilePartitionCommand)
