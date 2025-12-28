"""
服务模块：提供运行文档处理流水线的便捷接口。

包含三个入口函数：
- run_pipeline：按给定 YAML 配置运行任意流水线；
- run_generation：运行"生成"流水线；
- run_review：运行"评审"流水线。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import logging

import threading
import yaml
import os

# 新增：更健壮的资源定位（支持打包后的资源文件）
try:
    from importlib.resources import files as _pkg_files
except Exception:
    _pkg_files = None

# 使用共享 pipelines 解析工具
from triclick_doc_toolset.common.utils import resolve_pipelines_yaml

from triclick_doc_toolset.framework import Context, Pipeline

# 导入命令模块以确保命令注册
import triclick_doc_toolset.commands as commands

# 全局管线缓存：按配置文件绝对路径缓存构建好的 Pipeline
_PIPELINE_CACHE: Dict[str, Dict[str, Any]] = {}
_PIPELINE_CACHE_LOCK = threading.Lock()


logger = logging.getLogger(__name__)


def _configure_logging(level: str = "INFO") -> None:
    try:
        lvl = getattr(logging, str(level).upper(), logging.INFO)
    except Exception:
        lvl = logging.INFO
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=lvl,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        try:
            root.setLevel(lvl)
        except Exception:
            pass
        for h in list(root.handlers):
            try:
                h.setLevel(lvl)
            except Exception:
                pass
    logging.getLogger(__name__).setLevel(lvl)


def _configure_logging_from_env(default_level: str = "INFO") -> None:
    level = os.environ.get("TRICLICK_LOG_LEVEL", default_level)
    _configure_logging(level)


def _get_cached_pipeline(config_path: str) -> Pipeline:
    """
    获取缓存的 Pipeline；若缓存不存在或配置文件已变化，则重新构建并更新缓存。

    以配置文件的绝对路径作为缓存键，使用文件修改时间（mtime_ns）和大小（size）
    作为轻量级签名用于失效检测。
    """
    path = Path(config_path).resolve()
    stat = path.stat()
    key = str(path)
    with _PIPELINE_CACHE_LOCK:
        entry = _PIPELINE_CACHE.get(key)
        if entry and entry.get("mtime_ns") == stat.st_mtime_ns and entry.get("size") == stat.st_size:
            return entry["pipeline"]
        # 读取配置并构建新的 Pipeline
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        pipe = Pipeline.from_config(cfg)
        _PIPELINE_CACHE[key] = {
            "pipeline": pipe,
            "mtime_ns": stat.st_mtime_ns,
            "size": stat.st_size,
        }
        return pipe


def run_pipeline(
    config_path: str,
    document_path: str,
    output_dir: str,
    *,
    use_cache: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    按指定的 YAML 配置运行文档处理流水线。

    参数:
        config_path: 流水线配置文件路径（YAML）。
        document_path: 本地路径，支持单文件或文件夹。
        output_dir: 必填，输出目录。
        use_cache: 是否启用全局缓存（默认启用）。
    返回:
        以字典形式表示的流水线运行结果（JSON 兼容）。
    """
    # 配置日志：优先环境变量；verbose 显式提升到 INFO
    _configure_logging_from_env("INFO")
    if verbose:
        _configure_logging("INFO")

    raw = document_path.strip()
    if "," in raw:
        raise ValueError("document_path 仅支持本地单路径（文件或文件夹），不支持逗号分隔多文件")

    doc_file_path = Path(raw)
    if not doc_file_path.exists():
        raise FileNotFoundError(f"输入路径不存在: {doc_file_path}")

    # 构建运行上下文，记录待处理文档的 URI（文件或文件夹）
    ctx = Context()
    # 显式记录来源，便于下游命令兼容旧字段
    if doc_file_path.is_file():
        ctx.metadata["source_file"] = str(doc_file_path)
    else:
        ctx.metadata["source_dir"] = str(doc_file_path)
    # set document_uri
    ctx.set_document(uri=doc_file_path)

    # 指定输出目录（必填），供后续命令使用
    ctx.metadata["output_dir"] = output_dir

    # 获取管线对象：优先使用缓存
    if use_cache:
        pipe = _get_cached_pipeline(config_path)
    else:
        cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        pipe = Pipeline.from_config(cfg)
    # 执行流水线并获取结果
    result = pipe.run(ctx)
    # 将结果转换为 JSON 兼容的字典并返回
    result_json = result.to_json()
    if verbose:
        logger.info(json.dumps(result_json, ensure_ascii=False))
    return result_json


# 统一的管线配置文件定位方法
def _pipeline_yaml(name: str) -> str:
    # 委托给共享方法，保持 service.py 内部调用不变
    return resolve_pipelines_yaml(name)


def run_generation(document_path: str, output_dir: str, *, verbose: bool = False) -> Dict[str, Any]:
    """
    运行“生成（generation）”流水线。

    参数:
        document_path: 本地单路径，支持文件或文件夹；不支持逗号分隔多文件。
        output_dir: 必填，输出目录。

    返回:
        以字典形式表示的流水线运行结果（JSON 兼容）。

    说明:
        - 当输入为文件时，`metadata["source_file"]` 会被设置。
        - 当输入为文件夹时，`metadata["source_dir"]` 会被设置。
    """
    pipeline_yml_path = _pipeline_yaml("generation.yaml")
    return run_pipeline(pipeline_yml_path, document_path, output_dir, use_cache=True, verbose=verbose)


def run_review(document_path: str, output_dir: str, *, verbose: bool = False) -> Dict[str, Any]:
    """
    运行“评审（review）”流水线。

    参数:
        document_path: 本地单路径，支持文件或文件夹；不支持逗号分隔多文件。
        output_dir: 必填，输出目录。

    返回:
        以字典形式表示的流水线运行结果（JSON 兼容）。

    说明:
        - 当输入为文件时，`metadata["source_file"]` 会被设置。
        - 当输入为文件夹时，`metadata["source_dir"]` 会被设置。
    """
    pipeline_yml_path = _pipeline_yaml("review.yaml")
    return run_pipeline(pipeline_yml_path, document_path, output_dir, use_cache=True, verbose=verbose)