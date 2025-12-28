from __future__ import annotations

# 框架依赖
from triclick_doc_toolset.framework import Command, Context, CommandRegistry


class EnhanceLevelCommand(Command):
    """
    规范化 sections 的 level：当 level 为 0 且 local_path 非空时，将其设置为 1。
    """

    def is_satisfied(self, context: Context) -> bool:
        return bool(context.sections)

    def execute(self, context: Context) -> Context:
        sections = context.sections or []
        updated = 0

        for s in sections:
            try:
                lvl = int(s.get("level", 0))
            except Exception:
                lvl = 0
            if lvl == 0 and s.get("local_path"):
                s["level"] = 1
                updated += 1

        context.processing_summary["section_level_enhancement"] = {
            "applied": updated > 0,
            "updated_count": updated,
            "rule": "level_zero_with_local_path->set_one",
        }
        return context

# 注册到命令注册表
CommandRegistry.register("EnhanceLevelCommand", EnhanceLevelCommand)