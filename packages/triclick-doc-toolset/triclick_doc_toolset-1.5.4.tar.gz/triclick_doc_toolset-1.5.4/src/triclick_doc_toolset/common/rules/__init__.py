"""通用规则子包导出：统一暴露规则处理入口。"""

from .same_as_rule import apply_same_as_rule
from .normalize_duplicate_labels_rule import apply_normalize_duplicate_labels_rule

__all__ = [
    "apply_same_as_rule",
    "apply_normalize_duplicate_labels_rule",
]