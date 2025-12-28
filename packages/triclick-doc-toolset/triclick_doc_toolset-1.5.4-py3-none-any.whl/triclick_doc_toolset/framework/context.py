"""
Context
----------------
- 必需字段与方法：doc_type、document_uri、sections、metadata、errors、processing_summary、generated_files、individual_files、路径解析与错误记录。
- 移除 toc_tree、原文缓存、流式读取等非必须功能。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class Context:
    # 文档类型：例如 "docx"、"rtf" 等
    doc_type: Optional[str] = None
    # 文档来源：本地路径或 URI（支持单文件、文件夹、或多文件列表）
    document_uri: Optional[Union[Path, str, List[Union[Path, str]]]] = None
    # 元数据：通用属性字典（文件名、路径等）
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 错误列表：处理过程中的错误消息
    errors: List[str] = field(default_factory=list)
    # 解析出的文件列表（当输入为文件夹或多文件）
    individual_files: List[str] = field(default_factory=list)

    # 内容分段：由命令填充（标题/表格/脚注等结构化片段）
    sections: List[Dict[str, Any]] = field(default_factory=list)
    # 处理摘要：记录阶段性统计结果
    processing_summary: Dict[str, Any] = field(default_factory=dict)
    # 生成的文件路径列表
    generated_files: List[str] = field(default_factory=list)

    # --- 读写辅助方法（保持轻量） ---
    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any) -> "Context":
        if key == "metadata" and isinstance(value, dict):
            self.metadata.update(value)
        elif hasattr(self, key):
            setattr(self, key, value)
        else:
            self.metadata[key] = value
        return self

    def set_document(self, uri: Optional[Union[Path, str, List[Union[Path, str]]]] = None) -> "Context":
        """设置文档来源（单文件/文件夹/多文件列表），并预填解析出的文件集。"""
        if uri is not None:
            self.document_uri = uri
            try:
                files = self.resolve_document_paths()
                if files:
                    self.individual_files = [str(p) for p in files]
            except Exception as e:
                self.errors.append(f"resolve_document_paths failed: {e}")
        return self

    def has_document(self) -> bool:
        return self.document_uri is not None

    # --- 错误与输出 ---
    def add_error(self, error: str) -> "Context":
        self.errors.append(error)
        return self

    def add_generated_file(self, file_path: str) -> "Context":
        self.generated_files.append(file_path)
        return self

    def to_json(self) -> Dict[str, Any]:
        return {
            "doc_type": self.doc_type,
            "sections": self.sections,
            "metadata": self.metadata,
            "errors": self.errors,
            "individual_files": self.individual_files,
            "processing_summary": self.processing_summary,
            "generated_files": self.generated_files,
        }

    # --- 路径解析 ---
    def resolve_document_paths(self, *, recursive: bool = True, patterns: Optional[List[str]] = None) -> List[Path]:
        """解析并返回可处理的文件路径列表。

        支持以下输入：
        - 单文件路径：返回该文件；
        - 文件夹路径：按 patterns 枚举其中的文件；
        - 多文件路径列表：展开并去重；

        默认 patterns 为常见文档类型（docx/doc/pdf/md/txt），若未指定则列举所有普通文件。
        """
        exts_default = ["*.docx", "*.doc", "*.pdf", "*.md", "*.txt"]
        pats = patterns or exts_default

        def _expand_dir(dir_path: Path) -> List[Path]:
            files: List[Path] = []
            if recursive:
                for pat in pats:
                    files.extend(dir_path.rglob(pat))
            else:
                for pat in pats:
                    files.extend(dir_path.glob(pat))
            # 当 patterns 未指定时，仅返回默认扩展匹配结果，避免对整个目录做全量枚举
            return files

        uris = self.document_uri
        if uris is None:
            return []
        if isinstance(uris, list):
            paths: List[Path] = []
            for u in uris:
                p = Path(u)
                if p.is_dir():
                    paths.extend(_expand_dir(p))
                elif p.is_file():
                    paths.append(p)
            unique: List[Path] = []
            seen = set()
            for p in paths:
                rp = str(p.resolve())
                if rp not in seen and p.exists():
                    seen.add(rp)
                    unique.append(p)
            return unique
        else:
            p = Path(uris)
            if p.is_dir():
                return _expand_dir(p)
            return [p] if p.exists() else []