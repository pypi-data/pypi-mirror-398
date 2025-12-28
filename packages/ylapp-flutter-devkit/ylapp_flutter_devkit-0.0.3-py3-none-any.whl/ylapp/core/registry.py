"""命令注册器

职责：
- 维护命令名到命令实例的映射
- 提供 register/get/list 等操作
- 默认禁止重名覆盖（可通过 overwrite=True 覆盖），遇到重名输出日志警告
"""

from __future__ import annotations

from typing import Dict, List, Optional

import logging

from ylapp.core.command import Command


class CommandRegistry:
    """
    命令注册器

    约定：
    - 统一使用不含斜杠的小写名称作为键（例如 "help"）
    - 输入名称允许带前导斜杠（如 "/help"），会在内部规范化
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._cmds: Dict[str, Command] = {}
        self._logger = logger or logging.getLogger("ylapp.registry")

    @staticmethod
    def _normalize(name: str) -> str:
        """
        规范化命令名：去除前导斜杠、两端空白并小写
        """
        return name.lstrip("/").strip().lower()

    def register(self, cmd: Command, overwrite: bool = False) -> bool:
        """
        注册命令

        Args:
            cmd: 命令实例，要求 cmd.name 不含斜杠
            overwrite: 为 True 时允许覆盖同名命令

        Returns:
            bool: True 表示注册成功；False 表示因重名且未允许覆盖而忽略
        """
        key = self._normalize(cmd.name)
        if not key:
            raise ValueError("命令名称不能为空")
        exists = key in self._cmds
        if exists and not overwrite:
            self._logger.warning('命令已存在且未允许覆盖：%s', key)
            return False
        self._cmds[key] = cmd
        return True

    def get(self, name: str) -> Optional[Command]:
        """
        按名称获取命令（名称可含或不含前导斜杠）
        """
        key = self._normalize(name)
        return self._cmds.get(key)

    def list(self) -> List[Command]:
        """
        返回所有已注册命令，按名称排序
        """
        return sorted(self._cmds.values(), key=lambda c: c.name)

    def names(self) -> List[str]:
        """
        返回所有命令名称（规范化后），按字典序排序
        """
        return sorted(self._cmds.keys())

    def size(self) -> int:
        """
        返回已注册命令数量
        """
        return len(self._cmds)

    def __contains__(self, name: str) -> bool:
        """
        支持使用 `in` 判断名称是否已注册
        """
        return self._normalize(name) in self._cmds


__all__ = ["CommandRegistry"]