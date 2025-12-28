from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import re
import yaml
from functools import lru_cache

# 优先使用 importlib.resources 访问打包资源
try:
    from importlib.resources import files as _pkg_files
except Exception:
    _pkg_files = None


def resolve_pipelines_yaml(name: str) -> str:
    """解析包内 resources/pipelines 目录下 YAML 的本地文件路径。

    - 优先使用 `importlib.resources.files("triclick_doc_toolset").joinpath("resources", "pipelines", name)`；
    - 若资源不可直接作为文件（例如 zip 包），则抽取到临时目录后返回；
    - 开发模式（未打包）回退到仓库根的 `resources/pipelines/` 目录。
    """
    if not name:
        raise ValueError("name is required")

    # 1) 打包场景：通过 importlib.resources 定位
    if _pkg_files is not None:
        try:
            res = _pkg_files("triclick_doc_toolset").joinpath("resources", "pipelines", name)
            p_str = str(res)
            if Path(p_str).exists():
                return p_str
            # 资源不可直接映射为本地路径，抽取到临时目录
            import tempfile
            import shutil
            tmp_dir = Path(tempfile.gettempdir()) / "triclick-doc-toolset-pipelines"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_file = tmp_dir / name
            with res.open("rb") as fp_in, open(tmp_file, "wb") as fp_out:
                shutil.copyfileobj(fp_in, fp_out)
            return str(tmp_file)
        except Exception:
            # 回退到开发模式
            pass

    # 2) 开发场景：从源码路径回退（当前文件位于 src/triclick_doc_toolset/common/utils/...）
    repo_root = Path(__file__).resolve().parents[4]
    return str(repo_root / "resources" / "pipelines" / name)


# --- 以下为标题/标签/脚注正则加载逻辑，合并自 title_table_footnote_patterns_loader.py ---

def _resolve_config_path(config_path: Optional[str] = None) -> Path:
    """返回配置文件路径；若未提供，则指向包内 resources/pipelines/title_table_footnote_patterns.yaml"""
    if config_path:
        return Path(config_path)
    return Path(resolve_pipelines_yaml("title_table_footnote_patterns.yaml"))


def _load_patterns_from_yaml(key: str, config_path: Optional[str] = None, alt_key: Optional[str] = None) -> List[re.Pattern]:
    """通用 YAML 正则加载器：从指定 key（或后备 alt_key）加载字符串列表并编译为忽略大小写的正则。"""
    cfg_path = _resolve_config_path(config_path)
    patterns: List[str] = []
    try:
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            vals = data.get(key)
            if isinstance(vals, list):
                patterns = [p for p in vals if isinstance(p, str)]
            elif alt_key:
                one = data.get(alt_key)
                if isinstance(one, str) and one.strip():
                    patterns = [one.strip()]
    except Exception:
        patterns = []
    return [re.compile(p, re.IGNORECASE) for p in patterns]


@lru_cache(maxsize=8)
def load_title_patterns(config_path: Optional[str] = None) -> List[re.Pattern]:
    """从 YAML 加载标题匹配正则列表（`title_patterns`），忽略大小写。缺失时返回空列表。"""
    return _load_patterns_from_yaml("title_patterns", config_path)


@lru_cache(maxsize=8)
def load_label_patterns(config_path: Optional[str] = None) -> List[re.Pattern]:
    """从 YAML 加载用于提取最小标题标签的正则列表（`label_patterns` 或兼容 `title_label_pattern`）。"""
    return _load_patterns_from_yaml("label_patterns", config_path, alt_key="title_label_pattern")


@lru_cache(maxsize=8)
def load_footnote_patterns(config_path: Optional[str] = None) -> List[re.Pattern]:
    """从 YAML 加载脚注匹配正则列表（`footnote_patterns`），忽略大小写。缺失时返回空列表。"""
    return _load_patterns_from_yaml("footnote_patterns", config_path)