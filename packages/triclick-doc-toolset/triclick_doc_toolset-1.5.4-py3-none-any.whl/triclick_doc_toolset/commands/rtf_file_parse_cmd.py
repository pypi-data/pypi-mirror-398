from __future__ import annotations

from typing import List, Dict
from dataclasses import asdict
import time

from triclick_doc_toolset.framework import Command, Context, CommandRegistry
from triclick_doc_toolset.common.rtf import extract_rtf_content_with_metadata
from triclick_doc_toolset.common.utils import load_footnote_patterns
from triclick_doc_toolset.common.rules import apply_normalize_duplicate_labels_rule

class RtfFileParseCommand(Command):
    """RTF 解析命令

    解析输入的 `.rtf` 文件，提取“标题-表格-脚注”的分段元数据：
    - 复用统一的标题/标签/脚注正则与提取逻辑；
    - 过滤 `figure` 类型；
    - 支持规则：重复标签归一化。
    """

    def is_satisfied(self, context: Context) -> bool:
        return context.has_document()

    def execute(self, context: Context) -> Context:
        paths = context.resolve_document_paths(patterns=["*.rtf"])
        if not paths:
            context.add_error("No RTF files resolved from context")
            return context
        parsed: List[Dict] = []
        for p in paths:
            _start = time.perf_counter()
            # 预加载脚注模式以提升后续匹配效率
            _ = load_footnote_patterns()
            sections = extract_rtf_content_with_metadata(str(p))
            for sec in sections:
                try:
                    if (getattr(sec, "type", "") or "").strip().lower() == "figure":
                        continue
                except Exception:
                    pass
                d = asdict(sec)
                d["source_file"] = str(p)
                parsed.append(d)
            _elapsed = time.perf_counter() - _start
            context.processing_summary.setdefault("rtf_parse", []).append({"file": str(p), "elapsed": _elapsed})

        # 规则：重复标签归一化
        rule = next((r for r in self.rules if (r.get("name") == "normalize_duplicate_labels" and r.get("enabled") is True)), None)
        if rule:
            params = rule.get("params") or {}
            suffix_fmt = str(params.get("suffix_format", ".{n}"))
            apply_normalize_duplicate_labels_rule(parsed, suffix_fmt)

        # 写回上下文
        context.doc_type = "rtf"
        context.sections = parsed
        context.processing_summary["title_table_footnote_partition_rtf"] = {
            "files_processed": len(paths),
            "sections_extracted": len(parsed),
            "mode": "metadata_only",
        }
        return context

CommandRegistry.register("RtfFileParseCommand", RtfFileParseCommand)
