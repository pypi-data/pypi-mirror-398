from __future__ import annotations

import os
from pathlib import Path
from typing import List

from triclick_doc_toolset.common import TableItem
from triclick_doc_toolset.common.utils import slugify_text
from .rtf_text_util import iter_rtf_table_blocks

r"""RTF 拆分工具

按解析得到的分段元数据，将原始 RTF 中的表格块与标题/脚注拼接为独立 `.rtf` 文件：
- 保留原文档头（字体表/颜色表/页设置）；
- 表格块通过 `\trowd...\row` 边界进行拷贝；
- 脚注以段落 `\par` 形式追加到文件尾部；
- 输出路径包含源文件名与标签（避免冲突时追加序号）。
"""

def _unique_local_path(base_stem: str, label: str, output_dir: str, used_paths: set) -> str:
    """生成唯一输出路径，避免命名冲突"""
    safe = slugify_text(label)
    fname = f"{base_stem}.{safe}.rtf"
    path = os.path.join(output_dir, fname)
    n = 2
    while path in used_paths or os.path.exists(path):
        fname = f"{base_stem}#{safe}_{n}.rtf"
        path = os.path.join(output_dir, fname)
        n += 1
    used_paths.add(path)
    return path

def split_rtf_into_tables_with_copy(original_rtf_path: str, items: List[TableItem], output_dir: str) -> List[TableItem]:
    """基于索引信息从原始 RTF 拼接生成独立表格文件，并写回 `local_path`"""
    if not output_dir:
        raise ValueError("output_dir is required")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    p = Path(original_rtf_path)
    base_stem = p.stem
    raw = p.read_text(encoding="utf-8", errors="ignore")
    blocks = iter_rtf_table_blocks(raw)
    # 尝试抽取文档头部（在首个表格块之前的内容）
    head_end = blocks[0][0] if blocks else 0
    header = raw[:head_end] if head_end > 0 else raw[:raw.find("\\trowd")] if "\\trowd" in raw else raw.split("}")[0] + "\n"
    used: set = set()
    for sec in items:
        label = sec.get_section_label()
        out = [header]
        # 简化策略：当前版本复制首个到最后一个表格块的内容；后续可按 table_index 精细选择
        if blocks:
            out.append(raw[blocks[0][0]:blocks[-1][1]])
        # 追加脚注到尾部
        if sec.footnote:
            out.append("\n\\par " + sec.footnote + "\n")
        # 结束大括号
        out.append("}")
        local = _unique_local_path(base_stem, label, output_dir, used)
        Path(local).write_text("".join(out), encoding="utf-8")
        sec.local_path = local
    return items
