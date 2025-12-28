"""日志初始化与获取

功能：
- 配置统一日志格式与级别（默认 INFO），支持环境变量 YLAPP_LOG_LEVEL
- 提供获取命名日志记录器的便捷函数

格式：
- %(asctime)s %(levelname)s [%(name)s] %(message)s
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _resolve_level(level: Optional[str]) -> int:
    """解析日志级别字符串为 logging 等级整数（默认 INFO）"""
    if level is None:
        env = os.getenv("YLAPP_LOG_LEVEL", "INFO")
        return _LEVELS.get(env.upper(), logging.INFO)
    return _LEVELS.get(str(level).upper(), logging.INFO)


def configure_logging(level: Optional[str] = None, fmt: str = _DEFAULT_FORMAT) -> None:
    """配置全局日志（幂等，不重复添加处理器）

    Args:
        level: 日志级别（字符串，如 'INFO'），None 时读取环境变量 YLAPP_LOG_LEVEL
        fmt: 日志格式字符串
    """
    resolved = _resolve_level(level)
    root = logging.getLogger()
    root.setLevel(resolved)

    # 避免重复添加处理器：清理已存在的 StreamHandler 到 stdout
    new_handlers = []
    for h in root.handlers:
        if isinstance(h, logging.StreamHandler) and getattr(h, "_ylapp_stdout", False):
            # 已由我们配置过的处理器，跳过保留（也可以选择替换）
            continue
        new_handlers.append(h)
    root.handlers = new_handlers

    handler = logging.StreamHandler(stream=sys.stdout)
    handler._ylapp_stdout = True  # 标记为我们配置的处理器，避免重复
    handler.setLevel(resolved)
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)


def get_logger(name: str = "ylapp") -> logging.Logger:
    """获取命名日志记录器（在调用前应先执行 configure_logging）"""
    return logging.getLogger(name)


__all__ = ["configure_logging", "get_logger"]