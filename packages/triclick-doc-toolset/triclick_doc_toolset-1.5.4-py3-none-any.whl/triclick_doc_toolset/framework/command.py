from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List

from triclick_doc_toolset.framework.context import Context


class Command(ABC):
    name: str

    def __init__(
        self,
        name: Optional[str] = None,
        priority: int = 0,
        params: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable[[Context], bool]] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
    ):
        self.name = name or self.__class__.__name__
        self.priority = priority
        self.params = params or {}
        self.condition = condition
        # 新增：规则声明（不做兼容处理，命令自行识别并应用）
        self.rules: List[Dict[str, Any]] = list(rules or [])

    def check_condition(self, context: Context) -> bool:
        return True if self.condition is None else bool(self.condition(context))

    @abstractmethod
    def is_satisfied(self, context: Context) -> bool:
        raise NotImplementedError

    @abstractmethod
    def execute(self, context: Context) -> Context:
        raise NotImplementedError