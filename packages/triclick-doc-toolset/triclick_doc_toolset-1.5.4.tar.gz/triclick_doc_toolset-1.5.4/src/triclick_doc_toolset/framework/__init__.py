"""框架顶层导出模块：统一暴露核心类型与工厂方法。"""

from .context import Context
from .command import Command
from .strategy import Strategy, ExecMode
from .pipeline import Pipeline
from .command_registry import CommandRegistry

__all__ = [
    "Context",
    "Command",
    "Strategy",
    "ExecMode",
    "Pipeline",
    "CommandRegistry",
]