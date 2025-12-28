"""Data models for table parsing and processing."""

from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class TableItem:
    """表格项数据结构，包含标题、层级、索引和表格信息。

    增加字段:
    - type: 项类型，值为 'table' | 'listing' | 'figure'；优先依据 label 前缀推断，统一为小写。
    """
    type: str = "table"
    level: int = 0
    table_index: Optional[int] = None  # 表格索引，形如: 1/2/3/...
    label: Optional[str] = None        # 形如: table x.y.z（大小写不敏感）
    section: Optional[str] = None      # 形如: x.y.z
    title: Optional[str] = None        # 表格标题 Table x.y.z xxx
    same_as: bool = False              # 是否由 same-as 规则生成（复制目标表格文件并重命名）
    title_indices: List[int] = field(default_factory=list)
    footnote: Optional[str] = None
    footnote_indices: List[int] = field(default_factory=list)
    local_path: Optional[str] = None
    
    def set_table(self, table_index: int):
        """设置当前 section 的表格索引。"""
        self.table_index = table_index
    
    def add_footnote_index(self, para_index: int):
        """为当前 section 的表格追加脚注段落索引。"""
        self.footnote_indices.append(para_index)
    
    def append_footnote_text(self, text: str):
        """追加脚注文本（按段落累积，以换行分隔）。"""
        text = (text or "").strip()
        if not text:
            return
        if self.footnote:
            # 以换行分隔追加，保持原段落边界
            self.footnote += ("\n" if not self.footnote.endswith("\n") else "") + text
        else:
            self.footnote = text

    def get_section_label(self) -> str:
        """获取用于文件命名的标签，若无标签则返回默认值（由 type 决定）。"""
        if self.label:
            return self.label
        # 根据类型返回首字母大写的默认前缀
        prefix_map = {"table": "Table", "listing": "Listing", "figure": "Figure"}
        return prefix_map.get((self.type or "table").strip().lower(), "Table")

    def __post_init__(self):
        """在初始化后规范化并推断类型：优先依据 label，回退到传入类型。"""
        inferred = self._infer_type_from_label(self.label)
        t = (inferred or (self.type or "table")).strip().lower()
        self.type = t if t in {"table", "listing", "figure"} else "table"

    @staticmethod
    def _infer_type_from_label(label: Optional[str]) -> Optional[str]:
        """根据 label 的前缀推断类型（返回小写）。"""
        s = (label or "").strip().lower()
        if not s:
            return None
        # 取首个非空白 token
        prefix = s.split()[0]
        if prefix in {"table", "listing", "figure"}:
            return prefix
        return None