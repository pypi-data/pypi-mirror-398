from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable
import ast
from functools import lru_cache

from triclick_doc_toolset.framework.context import Context
from triclick_doc_toolset.framework.strategy import Strategy, ExecMode
from triclick_doc_toolset.framework.command_registry import CommandRegistry


class Pipeline:
    """管线（Pipeline）根据配置组织策略并执行，产出最终上下文。"""

    def __init__(self, strategies: List[Strategy]):
        # 优先级语义调整：数值越小越先执行
        self.strategies = sorted(strategies, key=lambda s: s.priority)

    def run(self, context: Context) -> Context:
        """按策略优先级顺序依次应用到上下文并返回结果。

        - 输入 `context` 作为初始上下文；
        - 依次调用每个策略的 `apply`，将上一步的上下文传递给下一步；
        - 返回最终处理完成的上下文。
        """
        ctx = context
        for strategy in self.strategies:
            ctx = strategy.apply(ctx)
        return ctx

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Pipeline":
        """根据 YAML/字典配置构建管线。

        - 读取策略列表，映射 `exec_mode` 为 `ExecMode`；
        - 命令创建通过 `CommandRegistry`；
        """
        # 基础校验
        _validate_config(config)
        # 初始化策略对象列表
        strategies: List[Strategy] = []
        # 读取顶层 pipeline 配置块，若不存在则使用空字典
        p_cfg: Dict[str, Any] = config.get("pipeline", {}) or {}
        # 读取策略配置列表，若不存在则为空列表
        strategies_cfg: List[Dict[str, Any]] = p_cfg.get("strategies", []) or []
        # 遍历每个策略配置并构建对应的 Strategy
        for s_cfg in strategies_cfg:
            # 策略名称（默认 "UnnamedStrategy"）
            name = s_cfg.get("name", "UnnamedStrategy")
            # 策略优先级（整数，数值越小越先执行）
            s_priority = int(s_cfg.get("priority", 0))

            # 执行模式枚举映射：将配置中的字符串转换为 ExecMode
            mode_str = s_cfg.get("exec_mode", ExecMode.SEQUENTIAL.value)
            try:
                # 尝试根据字符串创建对应的执行模式枚举值
                exec_mode = ExecMode(mode_str)
            except Exception:
                # 若映射失败，回退为顺序执行模式
                exec_mode = ExecMode.SEQUENTIAL

            # 当前策略的命令列表
            commands: List[Any] = []
            # 遍历该策略下的命令配置并创建命令实例
            for c_cfg in s_cfg.get("commands", []):
                # 命令类型名称（必填）
                type_name = c_cfg.get("type")
                if not type_name:
                    # 严格校验：缺少命令类型时直接抛错
                    raise ValueError("Command type is required in config")
                # 命令优先级（整数，数值越小越先执行）
                c_priority = int(c_cfg.get("priority", 0))
                # 命令的参数字典
                params = c_cfg.get("params", {})
                # 规则列表（严格区分于 params）
                rules = c_cfg.get("rules", [])
                # 通过命令注册表工厂创建命令实例
                c_name = c_cfg.get("name")
                cond_str: Optional[str] = c_cfg.get("condition")
                cond_fn: Optional[Callable[[Context], bool]] = _compile_condition(cond_str) if cond_str else None
                cmd = CommandRegistry.create(
                    type_name,
                    name=c_name,
                    priority=c_priority,
                    params=params,
                    condition=cond_fn,
                    rules=rules,
                )
                commands.append(cmd)

            # 将构建好的策略加入集合
            strategies.append(
                Strategy(
                    name=name,
                    priority=s_priority,
                    commands=commands,
                    exec_mode=exec_mode,
                )
            )

        # 返回管线实例（初始化时会按策略优先级排序）
        return cls(strategies)


@lru_cache(maxsize=128)
def _compile_condition(expr: Optional[str]) -> Optional[Callable[[Context], bool]]:
    if not expr:
        return None
    tree = ast.parse(expr, mode="eval")
    allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Eq,
        ast.NotEq,
        ast.In,
        ast.Is,
        ast.IsNot,
    )
    allowed_names = {"doc_type", "metadata", "sections"}
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported condition syntax: {type(node).__name__}")
        if isinstance(node, ast.Name):
            if node.id not in allowed_names:
                raise ValueError(f"Unsupported variable in condition: {node.id}")
    code = compile(tree, filename="<condition>", mode="eval")
    def _fn(ctx: Context) -> bool:
        locals_map = {
            "doc_type": ctx.doc_type,
            "metadata": ctx.metadata,
            "sections": ctx.sections,
        }
        return bool(eval(code, {"__builtins__": {}}, locals_map))
    return _fn


def _validate_config(config: Dict[str, Any]) -> None:
    p_cfg: Dict[str, Any] = config.get("pipeline", {}) or {}
    strategies_cfg: List[Dict[str, Any]] = p_cfg.get("strategies", []) or []
    for si, s_cfg in enumerate(strategies_cfg):
        s_name = s_cfg.get("name", f"strategy[{si}]")
        mode = s_cfg.get("exec_mode", ExecMode.SEQUENTIAL.value)
        if mode not in {ExecMode.SEQUENTIAL.value, ExecMode.PARALLEL.value}:
            raise ValueError(f"Invalid exec_mode in {s_name}: {mode}")
        try:
            int(s_cfg.get("priority", 0))
        except Exception:
            raise ValueError(f"Invalid priority in {s_name}: {s_cfg.get('priority')}")
        for ci, c_cfg in enumerate(s_cfg.get("commands", []) or []):
            c_name = c_cfg.get("name", f"command[{ci}]")
            if not c_cfg.get("type"):
                raise ValueError(f"Missing command.type in {s_name}/{c_name}")
            try:
                int(c_cfg.get("priority", 0))
            except Exception:
                raise ValueError(f"Invalid command.priority in {s_name}/{c_name}: {c_cfg.get('priority')}")