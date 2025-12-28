"""基础配置

提供默认配置与环境变量加载：
- 默认值：prompt="yl> ", banner="ylapp CLI (type /help for help)", log_level="INFO"
- 环境变量：YLAPP_PROMPT、YLAPP_BANNER、YLAPP_LOG_LEVEL
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Config:
    """全局配置对象"""
    prompt: str = "yl> "
    banner: str = "ylapp CLI (type /help for help)"
    log_level: str = "INFO"


def load_config() -> Config:
    """从环境变量加载配置，未设置则使用默认值"""
    return Config(
        prompt=os.getenv("YLAPP_PROMPT", "yl> "),
        banner=os.getenv("YLAPP_BANNER", "ylapp CLI (type /help for help)"),
        log_level=os.getenv("YLAPP_LOG_LEVEL", "INFO").upper(),
    )


__all__ = ["Config", "load_config"]