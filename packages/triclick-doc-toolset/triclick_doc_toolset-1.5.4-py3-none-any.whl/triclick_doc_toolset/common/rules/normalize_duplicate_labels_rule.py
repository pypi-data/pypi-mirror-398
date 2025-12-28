from __future__ import annotations

"""
normalize_duplicate_labels 规则工具：
- 对同一源文件中重复的 Table/Listing/Figure 标签追加递增序号后缀；
- 同步更新 section（编号部分）与 level（层级点数），并将标题中的前缀替换为新标签；

核心入口：
- apply_normalize_duplicate_labels_rule(items: List[Dict], suffix_fmt: str = ".{n}") -> List[Dict]
  就地更新并返回原列表，保持与命令层规则调用一致。
"""

import re
from typing import Dict, List


def apply_normalize_duplicate_labels_rule(items: List[Dict], suffix_fmt: str = ".{n}") -> List[Dict]:
    by_file: Dict[str, List[Dict]] = {}
    for d in items:
        by_file.setdefault(d.get("source_file") or "", []).append(d)

    for _, seq_items in by_file.items():
        counts: Dict[str, int] = {}
        for d in seq_items:
            label = (d.get("label") or "").strip()
            if label and re.match(r"(?i)^(table|listing|figure)\s+", label):
                counts[label] = counts.get(label, 0) + 1

        seq: Dict[str, int] = {}
        for d in seq_items:
            label = (d.get("label") or "").strip()
            if not label or counts.get(label, 0) <= 1:
                continue
            n = seq.get(label, 0) + 1
            seq[label] = n
            try:
                new_label = f"{label}{suffix_fmt}".replace("{n}", str(n))
            except Exception:
                new_label = f"{label}.{n}"

            # 更新 label/section/level/title
            d["label"] = new_label
            parts = new_label.split(None, 1)
            number_part = parts[1] if len(parts) == 2 else parts[0]
            d["section"] = number_part.strip()
            try:
                d["level"] = int(number_part.count("."))
            except Exception:
                pass

            title_text = (d.get("title") or "")
            if title_text:
                # 将标题中的前缀替换为新标签，例如："Table 4 Title X" -> "Table 4.1 Title X"
                try:
                    d["title"] = re.sub(r"(?i)^(?:[A-Za-z]\.|\d+\.)?\s*(table|listing|figure)\s+\S+", new_label, title_text)
                except Exception:
                    d["title"] = title_text

    return items