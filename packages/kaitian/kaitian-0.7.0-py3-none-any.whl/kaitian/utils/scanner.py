from __future__ import annotations

import base64
import hashlib
import logging
import os
import pickle
import platform
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)


def get_cache_directory(root: str | Path | None = None) -> Path:
    """获取缓存目录

    如果不提供根目录, 则根据平台类型自动加载标准缓存目录, 目前支持的有:

    - Windows: %LOCALAPPDATA% 或者 %TEMP%
    - MacOS: ~/Library/Caches
    - Linux: ~/.cache 或者 /tmp
    """
    cache_folder = (__package__ or "kaitian").split(".")[0]

    if root is not None:
        cache_dir = Path(root)
    else:
        system = platform.system()
        if system == "Windows":
            # Windows: %LOCALAPPDATA% or %TEMP%
            cache_dir = Path(os.environ.get("LOCALAPPDATA", "")) / cache_folder
            if not cache_dir.exists():
                cache_dir = Path(os.environ.get("TEMP", "")) / cache_folder
        elif system == "Darwin":  # macOS
            cache_dir = Path.home() / "Library" / "Caches" / cache_folder
        else:
            # Linux: ~/.cache or /tmp
            cache_dir = Path.home() / ".cache" / cache_folder
            if not cache_dir.exists():
                cache_dir = Path("/tmp") / cache_folder
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_file(identifier: str, root: str | Path | None = None) -> Path:
    """获取缓存文件路径

    根据 identifier 计算缓存文件名, identifier 可取数据源的绝对路径, 可保证本机唯一性.
    """
    cache_dir = get_cache_directory(root)
    hashf = hashlib.sha256()
    hashf.update(str(identifier).encode("utf-8"))
    cache_file = base64.urlsafe_b64encode(hashf.digest()).decode().rstrip("=").replace("-", "")
    return cache_dir / cache_file


def scan_csv(
    source: str | Path,
    *,
    try_parse_dates: bool = True,
    has_header: bool = True,
    skip_rows_after_header: int = 0,
    skip_rows: int = 0,
    n_rows: int | None = None,
    null_values: str | list[str] | dict[str, str] | None = None,
    separator: str = ",",
    comment_prefix: str | None = None,
    quote_char: str | None = '"',
    low_memory: bool = False,
    cache_folder: str | Path | None = None,
    schema_overrides: pl.Schema | dict[str, pl.DataType] | None = None,
    overwrite: bool = False,
    force: bool = False,
    **kwargs,
) -> pl.LazyFrame:
    """CSV 数据表扫描器.

    完整扫描 CSV 数据表并分析数据类型, 保留数据类型至缓存文件. 缓存文件信息包含 polars.Schema 和文件修改时间,
    缓存文件以 Pickle 格式保存, 格式为:

    {
        'mtime': file/modified/time,
        'schema': polars.Schema
    }
    """
    mtime = datetime.fromtimestamp(Path(source).stat().st_mtime)
    cache_file = get_cache_file(str(Path(source).absolute()), root=cache_folder)

    if not force and cache_file.exists():
        with open(cache_file, "rb") as f:
            cache: dict[str, Any] = pickle.load(f)
            if "mtime" not in cache or "schema" not in cache:
                logger.warning(f"缓存文件已损坏, 重新加载 Schema: {list(cache.keys())}")
                mtime_cache = mtime
                schema_cache = None
            else:
                mtime_cache = cache["mtime"]
                schema_cache = cache["schema"]
    else:
        mtime_cache = mtime
        schema_cache = None
        cache = {"mtime": mtime_cache, "schema": schema_cache}

    if mtime_cache is not None and schema_cache is not None:
        if mtime_cache == mtime:
            logger.debug(f"读取 Schema({len(schema_cache)}): {Path(source).parent.stem}/{Path(source).stem}")
            schema = schema_cache
        else:
            logger.debug("数据源已修改, 重新加载 Schema")
            schema = None
    else:
        schema = None

    if schema is None:
        schema = pl.scan_csv(
            source=source,
            infer_schema=True,
            infer_schema_length=None,
            try_parse_dates=try_parse_dates,
            has_header=has_header,
            skip_rows_after_header=skip_rows_after_header,
            skip_rows=skip_rows,
            n_rows=n_rows,
            null_values=null_values,
            separator=separator,
            comment_prefix=comment_prefix,
            quote_char=quote_char,
            low_memory=low_memory,
            schema_overrides=schema_overrides,
            **kwargs,
        ).collect_schema()
        logger.debug(f"分析 Schema({len(schema)}): {Path(source).parent.stem}/{Path(source).stem}")
        cache = {"mtime": mtime, "schema": schema}
        with open(cache_file, "wb") as f:
            pickle.dump(cache, f)
        logger.debug(f"Schema 缓存保存至: {cache_file}")
    else:
        if schema_overrides is not None:
            schema.update(pl.Schema(schema_overrides))
            if overwrite:
                with open(cache_file, "wb") as f:
                    pickle.dump(cache, f)
                logger.debug(f"覆盖后的 Schema 已写入: {cache_file}")
            else:
                logger.debug("执行临时覆盖, 覆盖后的 Schema 未保存")

    return pl.scan_csv(
        source,
        schema=schema,
        try_parse_dates=try_parse_dates,
        has_header=has_header,
        skip_rows_after_header=skip_rows_after_header,
        skip_rows=skip_rows,
        n_rows=n_rows,
        null_values=null_values,
        separator=separator,
        comment_prefix=comment_prefix,
        quote_char=quote_char,
        low_memory=low_memory,
        **kwargs,
    )
