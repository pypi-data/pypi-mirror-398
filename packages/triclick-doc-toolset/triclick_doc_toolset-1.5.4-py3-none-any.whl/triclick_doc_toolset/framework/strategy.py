from __future__ import annotations

from enum import Enum
from typing import List
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

from triclick_doc_toolset.framework.context import Context
from triclick_doc_toolset.framework.command import Command


class ExecMode(Enum):
    """策略执行模式枚举，约束为三种：顺序、并行、条件。"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行（当前实现按顺序运行，预留并行语义）


class Strategy:
    """策略（Strategy）用于组织一组命令并控制其执行方式。

    参数：
    - name: 策略名，便于定位与日志输出。
    - priority: 策略优先级，数值越小越先执行。
    - commands: 命令列表，按策略定义的方式执行。
    - exec_mode: 执行模式，使用 ExecMode 枚举。
    """

    def __init__(
        self,
        name: str,
        priority: int,
        commands: List[Command],
        exec_mode: ExecMode = ExecMode.SEQUENTIAL,
    ):
        self.name = name
        self.priority = priority
        # 优先级语义调整：命令按优先级升序（小值先执行）
        self.commands = sorted(commands, key=lambda c: c.priority)
        self.exec_mode = exec_mode

    def apply(self, context: Context) -> Context:
        """按照策略执行方式应用命令列表到上下文。"""
        if self.exec_mode == ExecMode.SEQUENTIAL:
            return self._execute_sequential(context)
        elif self.exec_mode == ExecMode.PARALLEL:
            return self._execute_parallel(context)
        else:
            raise ValueError(f"Unsupported execution mode: {self.exec_mode}")

    def _execute_sequential(self, context: Context) -> Context:
        ctx = context
        for cmd in self.commands:
            try:
                if not cmd.check_condition(ctx):
                    ctx.add_error(f"Command {cmd.name} skipped: condition not met")
                    continue
                if not cmd.is_satisfied(ctx):
                    ctx.add_error(f"Command {cmd.name} skipped: is_satisfied returned False")
                    continue
                start = time.perf_counter()
                ctx = cmd.execute(ctx)
                elapsed = time.perf_counter() - start
                logging.getLogger(__name__).info(f"[{cmd.name}] 耗时 {elapsed:.2f}s")
            except Exception as e:
                ctx.add_error(f"Command {cmd.name} failed: {e}")
        return ctx

    def _execute_parallel(self, context: Context) -> Context:
        base_ctx = context
        futures = []
        logger = logging.getLogger(__name__)
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(self.commands)))) as ex:
            for cmd in self.commands:
                snap = deepcopy(base_ctx)
                futures.append(
                    ex.submit(self._run_single_command, cmd, snap)
                )
            results: List[Context] = []
            for fut in as_completed(futures):
                try:
                    res_ctx, name, elapsed = fut.result()
                    logger.info(f"[{name}] 并行耗时 {elapsed:.2f}s")
                    results.append(res_ctx)
                except Exception as e:
                    base_ctx.add_error(f"Parallel command failed: {e}")
        return self._merge_contexts(base_ctx, results)

    @staticmethod
    def _run_single_command(cmd: Command, ctx: Context):
        start = time.perf_counter()
        try:
            if not cmd.check_condition(ctx):
                ctx.add_error(f"Command {cmd.name} skipped: condition not met")
                return ctx, cmd.name, time.perf_counter() - start
            if not cmd.is_satisfied(ctx):
                ctx.add_error(f"Command {cmd.name} skipped: is_satisfied returned False")
                return ctx, cmd.name, time.perf_counter() - start
            out = cmd.execute(ctx)
            elapsed = time.perf_counter() - start
            return out, cmd.name, elapsed
        except Exception as e:
            ctx.add_error(f"Command {cmd.name} failed: {e}")
            return ctx, cmd.name, time.perf_counter() - start

    @staticmethod
    def _merge_contexts(base: Context, contexts: List[Context]) -> Context:
        # doc_type：保留首个非空
        if base.doc_type is None:
            for c in contexts:
                if c.doc_type:
                    base.doc_type = c.doc_type
                    break
        # sections：追加去重
        seen = set()
        def _sig(d):
            try:
                return (
                    (d.get("source_file") or ""),
                    (d.get("label") or ""),
                    (d.get("section") or ""),
                    (d.get("local_path") or ""),
                )
            except Exception:
                return id(d)
        for d in base.sections:
            seen.add(_sig(d))
        for c in contexts:
            for d in c.sections or []:
                sig = _sig(d)
                if sig not in seen:
                    base.sections.append(d)
                    seen.add(sig)
        # processing_summary：浅合并（键覆盖）
        for c in contexts:
            try:
                base.processing_summary.update(c.processing_summary or {})
            except Exception:
                pass
        # errors：合并
        for c in contexts:
            for e in c.errors or []:
                base.add_error(e)
        # generated_files/individual_files：去重合并
        def _merge_list(dst, src):
            s = set(dst)
            for it in src or []:
                if it not in s:
                    dst.append(it)
                    s.add(it)
        for c in contexts:
            _merge_list(base.generated_files, c.generated_files)
        for c in contexts:
            _merge_list(base.individual_files, c.individual_files)
        return base