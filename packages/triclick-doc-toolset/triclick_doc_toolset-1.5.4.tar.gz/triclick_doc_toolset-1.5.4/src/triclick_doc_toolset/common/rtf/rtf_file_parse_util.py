from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from triclick_doc_toolset.common import TableItem
from triclick_doc_toolset.common.utils import (
    load_title_patterns,
    load_label_patterns,
    load_footnote_patterns,
)
from .rtf_text_util import rtf_to_plain_lines, iter_rtf_table_blocks
from triclick_doc_toolset.common.word.docx_file_parse_util import extract_title_label

"""RTF 解析工具

实现与 DOCX 等价的“标题-表格-脚注”解析，输出 `TableItem` 列表：
- 标题识别：复用 `title_patterns`，支持行首数字/字母枚举；
- 标签提取：复用 `extract_title_label`，统一大小写与空白；
- 表格判定：基于原始 RTF 中是否出现表格控制词（`\trowd`）；
- 脚注收集：匹配 `footnote_patterns` 或依据长度启发式。
"""

TITLE_PATTERNS: List[re.Pattern] = load_title_patterns()
LABEL_PATTERNS: List[re.Pattern] = load_label_patterns()
FOOTNOTE_PATTERNS: List[re.Pattern] = load_footnote_patterns()

def extract_rtf_content_with_metadata(rtf_path: str) -> List[TableItem]:
    """解析单个 RTF 文件，返回按顺序提取的分段元数据（TableItem 列表）

    优化要点：RTF 的标题通常位于表格首行的单元格中，因此：
    - 优先从首个表格块（\trowd...\row）抽取标题行；
    - 表格索引固定为 0（单文件单表格的常见场景）；
    - 脚注文本从最后一个表格块之后的正文抽取。
    """
    raw = Path(rtf_path).read_text(encoding="utf-8", errors="ignore")
    blocks = iter_rtf_table_blocks(raw)

    # 若不存在表格块，退化为基于全文的轻量解析（不推荐但保持兼容）
    if not blocks:
        lines = rtf_to_plain_lines(raw)
        # 查找首个标题行
        title_idx = next((i for i, ln in enumerate(lines) if any(pat.match(ln) for pat in TITLE_PATTERNS)), None)
        if title_idx is None:
            return []
        title_text = lines[title_idx]
        label = extract_title_label(title_text)
        section = None
        if label:
            parts = label.split(None, 1)
            section = (parts[1] if len(parts) == 2 else parts[0]).strip()
        item = TableItem(
            label=label,
            section=section,
            title=title_text,
            level=(section or "").count('.'),
            title_indices=[title_idx],
        )
        item.set_table(0)
        # 脚注启发式：标题之后的长行或 same-as 模式
        for i in range(title_idx + 1, len(lines)):
            t = (lines[i] or "").strip()
            if not t:
                continue
            if any(p.search(t) for p in FOOTNOTE_PATTERNS) or len(t) > 120:
                item.add_footnote_index(i)
                item.append_footnote_text(t)
        return [item]

    # 常规路径：首行表格块作为标题，之后的块为数据表；块尾之后为脚注
    first_start, first_end = blocks[0]
    title_lines = rtf_to_plain_lines(raw[first_start:first_end])
    # 组装标题：取首个命中标题模式的行及其后的非空行（限定最多 4 行）
    title_pos = next((i for i, ln in enumerate(title_lines) if any(pat.match(ln) for pat in TITLE_PATTERNS)), 0)
    assembled = []
    for i, ln in enumerate(title_lines[title_pos:title_pos + 6]):
        t = (ln or "").strip()
        if not t:
            continue
        assembled.append(t)
    full_title = "\n".join(assembled).strip()
    label = extract_title_label(assembled[0] if assembled else "")
    section = None
    if label:
        parts = label.split(None, 1)
        section = (parts[1] if len(parts) == 2 else parts[0]).strip()

    item = TableItem(
        label=label,
        section=section,
        title=full_title or (assembled[0] if assembled else ""),
        level=(section or "").count('.'),
        title_indices=list(range(title_pos, title_pos + len(assembled))),
    )
    item.set_table(0)

    # 脚注：取最后一个表格块之后的文本
    last_end = blocks[-1][1]
    tail_lines = rtf_to_plain_lines(raw[last_end:])
    for i, ln in enumerate(tail_lines):
        t = (ln or "").strip()
        if not t:
            continue
        if any(p.search(t) for p in FOOTNOTE_PATTERNS) or len(t) > 100:
            item.add_footnote_index(i)
            item.append_footnote_text(t)

    return [item]
