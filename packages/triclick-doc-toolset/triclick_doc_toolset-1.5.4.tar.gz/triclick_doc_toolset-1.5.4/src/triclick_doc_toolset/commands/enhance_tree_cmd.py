from __future__ import annotations

from typing import Any, Dict, List

# 框架依赖
from triclick_doc_toolset.framework import Command, Context, CommandRegistry


class EnhanceTreeCommand(Command):
    """
    补足层级父节点：
    - 遍历 context.sections，识别 "x.x.x"/"x.x.x.x" 等节点；
    - 若缺少对应父节点（分别为 "x.x"/"x.x.x"），则添加一个空父节点；
    - 父节点字段包含：type、level、table_index（若为 table 则取当前最大索引+1）、label、section、title；
    - 仅在 context.sections 非空时生效。
    """

    def is_satisfied(self, context: Context) -> bool:
        return bool(context.sections)

    def execute(self, context: Context) -> Context:
        sections: List[Dict[str, Any]] = context.sections or []
        if not sections:
            context.processing_summary["section_tree_enhancement"] = {
                "applied": False,
                "reason": "no_sections",
            }
            return context

        def _clean(s: Any) -> str:
            return str(s or "").strip()

        def _prefix(d: Dict[str, Any]) -> str:
            label = _clean(d.get("label"))
            if label:
                first = label.split()[0].capitalize()
                if first in {"Table", "Listing", "Figure"}:
                    return first
            typ = _clean(d.get("type")).lower()
            return {"table": "Table", "listing": "Listing", "figure": "Figure"}.get(typ, "Table")

        # 已有 section 集合（去重、便于存在性判断）
        existing = { _clean(d.get("section")) for d in sections if _clean(d.get("section")) }
        # 当前最大表格索引（用于为占位父节点分配 table_index）
        max_tbl_idx = -1
        for d in sections:
            ti = d.get("table_index")
            if isinstance(ti, int) and ti > max_tbl_idx:
                max_tbl_idx = ti

        added: List[Dict[str, Any]] = []
        for d in sections:
            sec = _clean(d.get("section"))
            if not sec:
                continue
            parts = [p for p in sec.split('.') if p]
            if len(parts) < 3:
                continue  # 仅处理 >= 三层的节点
            parent_sec = '.'.join(parts[:-1])
            if parent_sec in existing:
                continue

            pref = _prefix(d)
            parent_level = parent_sec.count('.')  # x.x -> 1, x.x.x -> 2
            parent: Dict[str, Any] = {
                "type": (d.get("type") or pref.lower()),
                "level": parent_level,
                "label": f"{pref} {parent_sec}",
                "section": parent_sec,
                "title": f"{pref} {parent_sec} Section",
            }
            # 仅对 table 类型分配 table_index（总数 + 1）
            if (parent.get("type") or "").strip().lower() == "table":
                max_tbl_idx += 1
                parent["table_index"] = max_tbl_idx

            added.append(parent)
            existing.add(parent_sec)

        suffix = str(self.params.get("dedup_section_suffix", ".h"))
        full = sections + added if added else sections
        seen: set = set()
        for d in full:
            sec = _clean(d.get("section"))
            if not sec:
                continue
            if sec in seen:
                d["section"] = f"{sec}{suffix}"
            else:
                seen.add(sec)
        context.sections = full
        if added:
            context.processing_summary["section_tree_enhancement"] = {
                "applied": True,
                "added_count": len(added),
                "parents": [a.get("section") for a in added],
            }
        else:
            context.processing_summary["section_tree_enhancement"] = {
                "applied": False,
                "reason": "no_missing_parent_nodes",
            }
        return context


# 注册到命令注册表
CommandRegistry.register("EnhanceTreeCommand", EnhanceTreeCommand)
