from __future__ import annotations

from typing import List, Optional, Dict
from docx import Document as DocxDocument
import re
from docx.text.paragraph import Paragraph


def normalize_docx_text(s: str) -> str:
    s = (s or "")
    s = s.replace("\u200b", "").replace("\xa0", " ")
    s = _RE_SPACES.sub(" ", s).strip()
    return s


_DOC_CACHE: Dict[str, DocxDocument] = {}
_PARA_TEXT_CACHE: Dict[str, List[str]] = {}
_PARA_FONT_CACHE: Dict[int, tuple] = {}
_PARA_TEXT_CACHE_HITS = 0
_PARA_TEXT_CACHE_MISSES = 0
_PARA_FONT_CACHE_HITS = 0
_PARA_FONT_CACHE_MISSES = 0

def assemble_title_lines(docx_path: str, indices: List[int], join_with: str = "\n") -> str:
    """
    按索引顺序拼接非空段落为标题，遇空行后停止；支持指定连接符。
    与现有命令中的标题组装保持一致语义，以统一入口。
    """
    try:
        paras = _PARA_TEXT_CACHE.get(docx_path)
        if paras is None:
            global _PARA_TEXT_CACHE_MISSES
            _PARA_TEXT_CACHE_MISSES += 1
            doc = _DOC_CACHE.get(docx_path)
            if doc is None:
                doc = DocxDocument(docx_path)
                _DOC_CACHE[docx_path] = doc
            paras = [normalize_docx_text(p.text) for p in doc.paragraphs]
            _PARA_TEXT_CACHE[docx_path] = paras
        else:
            global _PARA_TEXT_CACHE_HITS
            _PARA_TEXT_CACHE_HITS += 1
    except Exception:
        return ""
    parts: List[str] = []
    started = False
    separated = False
    for i in sorted(set(int(x) for x in (indices or []))):
        if i < 0 or i >= len(paras):
            continue
        text = paras[i]
        if not text:
            if started:
                separated = True
            continue
        if separated:
            break
        parts.append(text)
        started = True
    return join_with.join(parts).strip()


def extract_leading_enumerator(text: str) -> Optional[str]:
    """
    提取标题行首的枚举标记（支持“数字.”或“字母.”）。例如：
    "1. Table 4 ..." -> "1"；"A. Table 4 ..." -> "A"。
    返回去掉句点的枚举字符；未命中返回 None。
    """
    s = (text or "").strip()
    m = re.match(r"^\s*([0-9]+|[A-Za-z])\.", s)
    if m:
        return m.group(1)
    return None


def get_paragraph_font_info(para: Paragraph) -> tuple:
    """
    获取段落的字体信息 (font_name, font_size_pt, is_bold, is_italic, style_name)
    与解析器保持一致，以便跨模块统一判定标题续行与结构分隔。
    """
    font_name = None
    font_size = None
    is_bold = False
    is_italic = False
    style_name = None

    try:
        # 获取样式名称（安全访问）
        style = getattr(para, "style", None)
        if style and getattr(style, "name", None):
            style_name = style.name

        # 优先从 runs 获取字体信息（安全访问）
        for run in getattr(para, "runs", []):
            if getattr(run, "text", "").strip():  # 只考虑有内容的 run
                font = getattr(run, "font", None)
                if font:
                    name = getattr(font, "name", None)
                    size = getattr(font, "size", None)
                    bold = getattr(font, "bold", None)
                    italic = getattr(font, "italic", None)
                    if name and not font_name:
                        try:
                            font_name = (name or "").lower()
                        except Exception:
                            font_name = str(name).lower()
                    if size and not font_size:
                        font_size = getattr(size, "pt", None)
                    if bool(bold):
                        is_bold = True
                    if bool(italic):
                        is_italic = True
                break

        # 如果 runs 没有信息，从样式获取（安全访问）
        if not font_name or not font_size:
            style_font = getattr(style, "font", None)
            if style_font:
                s_name = getattr(style_font, "name", None)
                s_size = getattr(style_font, "size", None)
                if not font_name and s_name:
                    try:
                        font_name = (s_name or "").lower()
                    except Exception:
                        font_name = str(s_name).lower()
                if not font_size and s_size:
                    font_size = getattr(s_size, "pt", None)
    except Exception:
        # 保持容错，不影响后续逻辑
        pass

    return (font_name, font_size, is_bold, is_italic, style_name)


def is_structure_separator(para: Paragraph, base_font_info: tuple, para_index=None, title_start_index=None) -> bool:
    """
    判断段落是否为结构分隔符（空行、字体变化、或基于位置的启发式规则）。
    与解析器逻辑一致，抽到公共工具以统一续行判定。
    """
    text = (para.text or "").strip()

    # 空段落是明确的分隔符
    if not text:
        return True

    # 获取当前段落信息（带缓存）
    pid = id(para)
    current_font_info = _PARA_FONT_CACHE.get(pid)
    if current_font_info is None:
        global _PARA_FONT_CACHE_MISSES
        _PARA_FONT_CACHE_MISSES += 1
        current_font_info = get_paragraph_font_info(para)
        _PARA_FONT_CACHE[pid] = current_font_info
    else:
        global _PARA_FONT_CACHE_HITS
        _PARA_FONT_CACHE_HITS += 1
    base_name, base_size, base_bold, base_italic, base_style = base_font_info
    curr_name, curr_size, curr_bold, curr_italic, curr_style = current_font_info

    # 字体信息变化检测
    font_changed = False

    # 字体名称不同
    if base_name and curr_name and base_name != curr_name:
        font_changed = True

    # 字体大小差异超过 1pt
    if base_size and curr_size and abs(base_size - curr_size) > 1.0:
        font_changed = True

    # 粗体/斜体状态不同
    if base_bold != curr_bold or base_italic != curr_italic:
        font_changed = True

    # 样式名称不同
    if base_style and curr_style and base_style != curr_style:
        font_changed = True

    # 近标题容错：标题开始后前 4 行内，若不是典型脚注且文本不超长，则视为标题续行
    if font_changed:
        if para_index is not None and title_start_index is not None:
            if para_index - title_start_index <= 4:
                if not _is_probable_footnote(text, curr_style) and len(text) <= 150:
                    return False
        return True

    # 当字体信息都为空时，使用启发式规则
    if not any([base_name, base_size, curr_name, curr_size]):
        # 基于段落位置的启发式判断
        if para_index is not None and title_start_index is not None:
            # 如果当前段落距离标题开始位置超过 4 行，很可能是脚注
            if para_index - title_start_index > 4:
                return True

        # 基于内容的启发式判断
        # 如果段落包含典型的脚注标识符
        if _is_probable_footnote(text, curr_style):
            return True

        # 如果段落很长（超过 100 字符），很可能是脚注
        if len(text) > 100:
            return True

    return False


def _is_probable_footnote(text: str, style_name: str) -> bool:
    """
    判断段落是否很可能是脚注文本。
    规则：项目符号/破折号开头；排除 Heading。
    注：更严格的 FOOTNOTE_PATTERNS 在解析器中使用；此处提供通用启发式。
    """
    if not text:
        return False
    if style_name and style_name.startswith('Heading'):
        return False
    if re.match(r"^[\-•·–]\s+", text):
        return True
    return False


def is_toc_like_paragraph(text: str, style_name: str) -> bool:
    """
    判定段落是否类似 TOC 目录行：
    - 样式为 TOC（如 "TOC Heading"/"TOC 1"/"TOC 2" 等）；
    - 或文本形如 "Table X.Y ... <tab/dots> <page>"。
    """
    s = normalize_docx_text(text)
    if not s:
        return False
    sty = (style_name or "").strip().lower()
    if sty.startswith("toc") or sty in {"toc heading", "toc 1", "toc 2", "toc 3"}:
        return True
    raw = text or ""
    has_tab = "\t" in raw
    ends_with_page = bool(re.search(r"\b\d{1,4}\s$", raw))
    return bool(TOC_LINE_PAT.match(raw)) or (has_tab and ends_with_page)
_RE_SPACES = re.compile(r"\s+")
TOC_LINE_PAT = re.compile(r"(?i)^(?:table|listing|figure|section)\s+[A-Za-z0-9._-]+(?:\.[A-Za-z0-9._-]+)*\s*(?:\t|\s{2,}|[.\u2026]{3,})\s*\d{1,4}\s$")


def get_title_util_cache_stats() -> Dict[str, int]:
    return {
        "para_text_cache_hits": int(_PARA_TEXT_CACHE_HITS),
        "para_text_cache_misses": int(_PARA_TEXT_CACHE_MISSES),
        "para_text_cache_size": int(len(_PARA_TEXT_CACHE)),
        "para_font_cache_hits": int(_PARA_FONT_CACHE_HITS),
        "para_font_cache_misses": int(_PARA_FONT_CACHE_MISSES),
        "para_font_cache_size": int(len(_PARA_FONT_CACHE)),
    }


def clear_title_util_caches(docx_path: Optional[str] = None) -> None:
    if docx_path:
        _DOC_CACHE.pop(docx_path, None)
        _PARA_TEXT_CACHE.pop(docx_path, None)
    _PARA_FONT_CACHE.clear()