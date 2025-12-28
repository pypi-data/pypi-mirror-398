"""
命令注册表（CommandRegistry）模块
--------------------------------
本模块维护命令类型到类的映射，支持注册、查找与基于配置的实例化。
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type, Callable
from triclick_doc_toolset.framework.command import Command
from triclick_doc_toolset.framework.context import Context


class CommandRegistry:
    """命令注册表，用于集中管理命令类型与创建。"""
    _cmd_bus: Dict[str, Type[Command]] = {}

    @classmethod
    def register(cls, type_name: str, command_cls: Type[Command]) -> None:
        """注册命令类型到类。"""
        cls._cmd_bus[type_name] = command_cls

    @classmethod
    def get(cls, type_name: str) -> Optional[Type[Command]]:
        """根据类型名获取命令类。"""
        return cls._cmd_bus.get(type_name)

    @classmethod
    def create(
        cls,
        type_name: str,
        *,
        name: Optional[str] = None,
        priority: int = 0,
        params: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable[[Context], bool]] = None,
        rules: Optional[list] = None,
    ) -> Command:
        command_cls = cls.get(type_name)
        if not command_cls:
            raise ValueError(f"Unknown command type: {type_name}")
        return command_cls(name=name, priority=priority, params=params, condition=condition, rules=rules)