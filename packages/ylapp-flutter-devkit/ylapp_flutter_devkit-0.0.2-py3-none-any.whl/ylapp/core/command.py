"""命令抽象与执行上下文定义

本模块提供：
- Command 抽象基类：统一命令的名称、描述与执行接口
- CommandContext 执行上下文：封装一条输入被解析后的环境数据（原始输入、参数、IO等）

设计约定：
- 所有斜杠命令实现需继承 Command 并实现 execute(ctx) 方法
- ctx.io 提供 readline/write 能力；config/logger/registry 为可选扩展对象
- 命令实现不应进行耗时阻塞操作（后续可扩展异步与任务队列）
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Protocol, runtime_checkable
import logging


@runtime_checkable
class IO(Protocol):
    """IO 抽象：为 REPL/命令提供输入输出能力"""

    def readline(self, prompt: str) -> str:
        """读取一行用户输入（带提示符）"""
        ...

    def write(self, text: str) -> None:
        """输出一段文本到终端"""
        ...


@dataclass
class CommandContext:
    """命令执行上下文

    Attributes:
        raw_input: 原始用户输入（例如 "/help arg1 arg2"）
        args: 解析后的参数列表（不含命令名与前导斜杠）
        io: IO 抽象实例，用于与终端交互
        config: 全局配置对象（可选），例如提示符、欢迎语、日志级别等
        logger: 日志记录器（可选），建议命令实现使用此记录器输出诊断信息
        registry: 命令注册器（可选），可用于在命令内部查询其它命令的元信息
    """

    raw_input: str
    args: List[str]
    io: IO
    config: Any | None = None
    logger: logging.Logger | None = None
    registry: Any | None = None


class Command(ABC):
    """命令抽象基类

    约束：
    - 子类必须定义 name 与 description 两个属性，并实现 execute(ctx)
    - name 采用不含斜杠的短名称（例如 "help"），实际路由时由上层在前面补 "/"
    - execute 返回需要展示给用户的文本（若无输出可返回空字符串）
    """

    name: str
    description: str

    def __init__(self, name: str, description: str) -> None:
        """初始化命令元信息

        Args:
            name: 命令名称（不含斜杠），如 "help"
            description: 命令简要说明
        """
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, ctx: CommandContext) -> str:
        """执行命令

        Args:
            ctx: 命令执行上下文，包含原始输入、参数、IO、配置、日志与注册器

        Returns:
            需要输出到终端的文本字符串；若无输出可返回空字符串
        """
        raise NotImplementedError


__all__ = ["IO", "CommandContext", "Command"]