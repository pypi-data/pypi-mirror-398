"""RTF 文本工具

本模块提供 RTF 原始文本的轻量解析能力：
- `normalize_rtf_text`：清洗空白字符，规范化文本；
- `rtf_to_plain`：将 RTF 控制词/转义符转换为可读纯文本；
- `rtf_to_plain_lines`：按行拆分纯文本并进行规范化；
- `iter_rtf_table_blocks`：识别并返回表格块在原始 RTF 字符串中的边界。

说明：为保持最小依赖与高可用性，未引入第三方 RTF 解析库，使用正则进行轻量识别。
"""
import re

_RE_SPACES = re.compile(r"\s+")

def normalize_rtf_text(s: str) -> str:
    """规范化 RTF 文本中的空白与不可见字符"""
    s = (s or "")
    s = s.replace("\u200b", "").replace("\xa0", " ")
    s = _RE_SPACES.sub(" ", s).strip()
    return s

def rtf_to_plain(rtf: str) -> str:
    """将 RTF 控制词转换为可读纯文本，保留换行与制表结构"""
    s = rtf or ""
    s = s.replace("\tab", "\t")
    s = re.sub(r"\\line", "\n", s)
    s = re.sub(r"\\par", "\n", s)
    s = re.sub(r"\\[^\\\s{}]+(?:-?\d+)?", "", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\n+", "\n", s)
    return s

def rtf_to_plain_lines(rtf: str) -> list[str]:
    """拆分为规范化的纯文本行，便于标题/脚注识别"""
    text = rtf_to_plain(rtf)
    lines = [normalize_rtf_text(x) for x in text.split("\n")]
    return [x for x in lines if x is not None]

def iter_rtf_table_blocks(rtf: str) -> list[tuple[int, int]]:
    """识别 RTF 中的表格块边界（从 `\trowd` 到对应 `\row`）并返回 (start, end) 列表"""
    blocks = []
    i = 0
    while True:
        m = re.search(r"\\trowd", rtf[i:])
        if not m:
            break
        start = i + m.start()
        m2 = re.search(r"\\row", rtf[start:])
        if not m2:
            break
        end = start + m2.end()
        blocks.append((start, end))
        i = end
    return blocks
