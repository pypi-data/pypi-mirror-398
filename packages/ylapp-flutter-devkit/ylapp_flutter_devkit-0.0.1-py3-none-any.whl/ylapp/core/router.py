"""命令路由

职责：
- 解析以 "/" 开头的输入行，提取命令名与位置参数
- 根据注册器检索命令，构造执行上下文并调用命令
- 对未知命令与异常提供友好提示

约定：
- 命令名统一使用不含斜杠的小写名称（例如 "help"）
- 位置参数通过空格拆分，后续可扩展为 --key=value 格式
"""

from __future__ import annotations

from typing import List, Tuple, Optional
import logging

from ylapp.core.command import CommandContext
from ylapp.core.registry import CommandRegistry


class Router:
    """命令路由器"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger("ylapp.router")

    @staticmethod
    def _normalize(name: str) -> str:
        """
        规范化命令名：去除前导斜杠、两端空白并小写
        """
        return name.lstrip("/").strip().lower()

    @staticmethod
    def _parse(line: str) -> Tuple[str, List[str]]:
        """
        解析输入行，返回 (命令名, 参数列表)

        规则：
        - 仅当行以 "/" 开头时进行解析
        - 第一段作为命令名，其余作为位置参数
        """
        raw = (line or "").strip()
        if not raw.startswith("/"):
            return "", []
        parts = raw.split()
        if not parts:
            return "", []
        name = Router._normalize(parts[0])
        args = parts[1:]
        return name, args

    def route(self, line: str, registry: CommandRegistry, base_ctx: CommandContext) -> str:
        """
        路由执行：解析命令并分发给注册器中的具体命令

        行为：
        - 若命令名为空或命令不存在，返回友好提示并引导输入 /help
        - 构建新的 CommandContext（保留 IO/Config/Logger/Registry），传入解析出的参数与原始输入
        - 捕获执行异常并返回错误信息，同时记录日志
        """
        name, args = self._parse(line)
        if not name:
            return "未知命令，输入 /help 查看可用命令"

        cmd = registry.get(name)
        if not cmd:
            return f"未知命令：/{name}\n输入 /help 查看可用命令"

        ctx = CommandContext(
            raw_input=line,
            args=args,
            io=base_ctx.io,
            config=base_ctx.config,
            logger=base_ctx.logger,
            registry=registry,
        )

        try:
            result = cmd.execute(ctx)
            return result or ""
        except Exception as exc:
            if base_ctx.logger:
                base_ctx.logger.exception("命令执行异常：/%s", name)
            return f"命令执行错误：{exc}"


__all__ = ["Router"]