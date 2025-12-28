"""帮助命令（/help）

功能：
- 列出所有已注册命令及其释义
- 支持查看指定命令的详细信息：/help name
"""

from __future__ import annotations

from typing import List

from ylapp.core.command import Command, CommandContext


class HelpCommand(Command):
    """显示命令清单与说明"""

    def __init__(self) -> None:
        
        super().__init__(name="h", description="显示支持的命令清单与释义")

    def execute(self, ctx: CommandContext) -> str:
        registry = ctx.registry
        if registry is None:
            return "命令注册器未初始化"

        args: List[str] = ctx.args or []
        # 查看指定命令详情：/help name
        if args:
            target = args[0].lstrip("/").strip().lower()
            cmd = registry.get(target)
            if cmd:
                return f"/{cmd.name} - {cmd.description}"
            return f"未找到命令：/{target}"

        # 列出所有命令
        commands = registry.list()
        if not commands:
            return "暂无可用命令"

        lines = ["可用命令："]
        for c in commands:
            lines.append(f"/{c.name} - {c.description}")
        return "\n".join(lines)


def register(registry) -> None:
    """注册帮助命令到注册器"""
    registry.register(HelpCommand())


__all__ = ["HelpCommand", "register"]