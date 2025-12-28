from __future__ import annotations

"""
same-as/repeat 规则工具：
- 当某个 section 的脚注包含 "Same as Table X.Y"（或 Listing），表示该 section 内容与目标表格一致。
- 需要复制目标表格的拆分文件，替换标题为当前 section 的标题，并将文件名改为当前 section 的 label。

使用前提：
- 已调用 split_docx_into_tables_with_copy 生成了各表格的拆分文件，并写回了 TableItem.local_path。

核心入口：
- apply_same_as_rule(docx_content: List[TableItem]) -> List[TableItem]
  遍历 docx_content，将含有 Same-as 的且无表格的 section，复制目标拆分文件并更新 local_path。
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import io
from collections import OrderedDict
from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph

from triclick_doc_toolset.common import TableItem
from triclick_doc_toolset.common.word.docx_file_parse_util import extract_title_label
from triclick_doc_toolset.common.utils import load_footnote_patterns, slugify_text


def _slugify(text: str) -> str:
    """与拆分工具保持一致：空白转下划线，移除非字母数字/点/横线字符，并折叠连续下划线。"""
    return slugify_text(text)


def _unique_local_path(base_stem: str, label: str, output_dir: str, used_paths: set) -> str:
    """生成唯一输出路径，与拆分逻辑保持一致。"""
    safe_label = _slugify(label)
    fname = f"{base_stem}.{safe_label}.docx"
    path = os.path.join(output_dir, fname)
    counter = 2
    while path in used_paths or os.path.exists(path):
        fname = f"{base_stem}#{safe_label}_{counter}.docx"
        path = os.path.join(output_dir, fname)
        counter += 1
    used_paths.add(path)
    return path


def _normalize_label(label: Optional[str]) -> Optional[str]:
    """统一标签大小写与空白：'table 1.2' -> 'Table 1.2'（支持 Listing/Figure）。"""
    if not label:
        return None
    s = re.sub(r"\s+", " ", label.strip())
    s = re.sub(r"^(table|listing|figure)", lambda m: m.group(1).capitalize(), s, flags=re.I)
    return s


def _extract_same_as_target_label(text: Optional[str]) -> Optional[str]:
    """
    从脚注文本中提取同表复用目标标签：
    - 依据 YAML 配置的脚注模式（same as/repeat + Table/Listing/Figure）判断是否匹配；
    - 若命中，再从文本中提取标签（例如 "Table 2.2.1"）。
    """
    if not text:
        return None
    s = (text or "").strip()
    # 宽松归一化空白：将常见的非断行空格/窄空格等统一为普通空格，并折叠连续空白
    # 以提升正则中 \s+ 的命中率（例如 "Repeat\u00A0table 2.2.1"）
    s = re.sub(r"[\u00A0\u2007\u202F]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    # 用配置化的脚注模式判断是否属于 same-as/repeat 类型
    footnote_patterns = load_footnote_patterns()
    if not any(p.search(s) for p in footnote_patterns):
        return None
    # 标签提取允许在任意位置出现（由 extract_title_label 负责）
    return extract_title_label(s)


_DOCX_BYTES_CACHE: OrderedDict[str, bytes] = OrderedDict()
_DOCX_BYTES_CACHE_MAX = 16
_DOCX_BYTES_CACHE_HITS = 0
_DOCX_BYTES_CACHE_MISSES = 0
_LAST_USED_REF_PATHS: set[str] = set()


def _get_doc_bytes(path: str) -> bytes:
    b = _DOCX_BYTES_CACHE.get(path)
    if b is not None:
        # LRU 触达，移到末尾
        try:
            _DOCX_BYTES_CACHE.move_to_end(path)
        except Exception:
            pass
        global _DOCX_BYTES_CACHE_HITS
        _DOCX_BYTES_CACHE_HITS += 1
        return b
    with open(path, "rb") as f:
        b = f.read()
    global _DOCX_BYTES_CACHE_MISSES
    _DOCX_BYTES_CACHE_MISSES += 1
    _DOCX_BYTES_CACHE[path] = b
    try:
        if len(_DOCX_BYTES_CACHE) > _DOCX_BYTES_CACHE_MAX:
            _DOCX_BYTES_CACHE.popitem(last=False)
    except Exception:
        pass
    return b


def _get_base_stem_and_output_dir(ref_path: str) -> Tuple[str, str]:
    """根据已存在的拆分文件推导 base_stem 与输出目录。"""
    p = Path(ref_path)
    name = p.name  # 形如: <base_stem>.<safe_label>.docx 或 <base_stem>#<safe_label>_N.docx
    # 优先按 '#' 切分（计数版本），否则按 '.' 切分（基础版本）
    base_stem = name.split("#", 1)[0].split(".", 1)[0]
    return base_stem, str(p.parent)


def _replace_leading_title(doc: DocxDocument, new_title: str):
    """
    将文档中表格之前的所有标题段落替换为 new_title。
    - 若存在多个标题段落，仅第一个替换为新标题，其余清空文本。
    - 不改变段落样式，仅替换文本内容。
    """
    body = doc._element.body
    first = True
    for child in body.iterchildren():
        if isinstance(child, CT_Tbl):
            break
        if isinstance(child, CT_P):
            para = Paragraph(child, doc)
            if first:
                para.text = (new_title or "").strip()
                first = False
            else:
                # 避免多余旧标题残留
                para.text = ""


def apply_same_as_rule(docx_content: List[TableItem]) -> List[TableItem]:
    """
    应用 "Same as Table/Listing" 规则：
    - 对于无表格的 section，若脚注包含 "Same as Table X.Y"，则复制目标表格的拆分文件，
      将标题替换为当前 section 标题，并按当前 label 命名新文件，更新 current.local_path。

    参数:
    - docx_content: 解析并拆分后的 TableItem 列表；其中有表格的项应已写入 local_path。

    返回: 更新后的 docx_content。
    """
    # 建立 label -> 拆分文件路径 的映射（仅限已生成文件的表格项）
    label_to_path: dict[str, str] = {}
    used_paths: set = set()
    for sec in docx_content:
        if sec.local_path:
            used_paths.add(sec.local_path)
        if sec.table_index is not None and sec.label and sec.local_path:
            norm = _normalize_label(sec.label)
            if norm:
                label_to_path[norm] = sec.local_path

    # 遍历需要应用 same-as 的 section，生成结果列表
    result: List[TableItem] = []
    for sec in docx_content:
        # 有表格的 section 始终保留
        if sec.table_index is not None:
            result.append(sec)
            continue
        # 无表格：检查是否 same-as
        target_label = _extract_same_as_target_label(sec.footnote)
        if not target_label:
            result.append(sec)
            continue
        target_label = _normalize_label(target_label)
        if target_label is None:
            result.append(sec)
            continue
        ref_path = label_to_path.get(target_label)
        if not ref_path or not os.path.exists(ref_path):
            # same-as 目标不存在：忽略当前节点并删除其占位输出文件
            try:
                if sec.local_path and os.path.exists(sec.local_path):
                    os.remove(sec.local_path)
                    logging.getLogger(__name__).warning(
                        f"Same-as ignored: '{sec.label or sec.title or ''}' -> target '{target_label}' not found; removed {sec.local_path}"
                    )
            except Exception:
                pass
            continue

        # 复制并替换标题
        ref_doc = Document(io.BytesIO(_get_doc_bytes(ref_path)))
        try:
            _LAST_USED_REF_PATHS.add(ref_path)
        except Exception:
            pass
        # 新标题：优先使用当前 section.title；其次尝试由标题提取 label；再退化为 target_label
        new_title = (sec.title or "").strip()
        if not new_title:
            # 尝试从标题中提取简洁标签
            inferred = extract_title_label(sec.title or "")
            new_title = inferred or target_label or ""
        _replace_leading_title(ref_doc, new_title)

        # 新文件名标签：优先当前 sec.label；其次从标题提取；再退化 target_label
        new_label = _normalize_label(sec.label) or extract_title_label(sec.title or "") or target_label or "Table"

        base_stem, output_dir = _get_base_stem_and_output_dir(ref_path)
        new_path = _unique_local_path(base_stem, new_label, output_dir, used_paths)
        ref_doc.save(new_path)

        # 若此前已为该无表格 section 生成占位文件，删除以避免冗余
        try:
            if sec.local_path and sec.local_path != new_path and os.path.exists(sec.local_path):
                os.remove(sec.local_path)
        except Exception:
            pass

        # 写回当前 section 的输出路径，并标记为 same-as 生成
        sec.same_as = True
        sec.local_path = new_path
        
        # 可选：日志输出
        logging.getLogger(__name__).info(
            f"Same-as applied: '{new_label}' -> {new_path} (from {target_label})"
        )

        # 保留命中 same-as 的节点到结果集合，避免在 sections 中被忽略
        result.append(sec)

    # 清理本轮使用的缓存，控制内存占用
    try:
        for p in list(_LAST_USED_REF_PATHS):
            _DOCX_BYTES_CACHE.pop(p, None)
        _LAST_USED_REF_PATHS.clear()
    except Exception:
        pass
    return result


def get_bytes_cache_stats() -> dict:
    return {
        "docx_bytes_cache_hits": int(_DOCX_BYTES_CACHE_HITS),
        "docx_bytes_cache_misses": int(_DOCX_BYTES_CACHE_MISSES),
        "docx_bytes_cache_size": int(len(_DOCX_BYTES_CACHE)),
    }