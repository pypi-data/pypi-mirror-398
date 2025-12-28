"""REPL 主循环

职责：
- 打印欢迎横幅与提示符，持续读取用户输入
- 以 "/" 开头的输入交由 Router 解析并执行对应命令
- 非命令输入作为普通文本 echo 输出（为未来 Agent 集成预留）
- 支持 Ctrl+C 优雅退出；异常不崩溃并输出错误信息

依赖：
- ylapp.core.command.CommandContext
- ylapp.core.registry.CommandRegistry
- ylapp.core.router.Router
- ylapp.core.io.StdIO（或任意满足 IO 协议的实现）
- ylapp.core.config.Config
- ylapp.core.logger（可选）

使用示例（后续任务会在 CLI 中接入）：
    io = StdIO()
    config = load_config()
    configure_logging(config.log_level)
    logger = get_logger("ylapp.repl")
    registry = CommandRegistry(logger)
    router = Router(logger)
    repl = Repl(io, router, registry, config, logger)
    repl.run()
"""

from __future__ import annotations

from typing import Optional
import logging

from ylapp.core.command import CommandContext, IO
from ylapp.core.registry import CommandRegistry
from ylapp.core.router import Router
from ylapp.core.config import Config


class Repl:
    """交互式 REPL 主循环"""

    def __init__(
        self,
        io: IO,
        router: Router,
        registry: CommandRegistry,
        config: Config,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.io = io
        self.router = router
        self.registry = registry
        self.config = config
        self.logger = logger or logging.getLogger("ylapp.repl")

    def run(self) -> None:
        """运行 REPL 循环"""
        # 欢迎横幅
        try:
            self.io.write(self.config.banner)
        except Exception:
            # 输出失败不影响循环
            pass

        while True:
            try:
                line = self.io.readline(self.config.prompt)
                # 输入流结束（EOF）时：继续下一轮或由上层决定退出
                if line is None:
                    line = ""
                if not str(line).strip():
                    # 空行：继续下一轮
                    continue

                if str(line).startswith("/"):
                    base_ctx = CommandContext(
                        raw_input=str(line),
                        args=[],  # 具体参数将在 Router 中解析填充
                        io=self.io,
                        config=self.config,
                        logger=self.logger,
                        registry=self.registry,
                    )
                    text = self.router.route(str(line), self.registry, base_ctx)
                    if text:
                        self.io.write(text)
                else:
                    # 非命令输入：作为普通消息 echo 输出
                    self.io.write(f"[echo] {line}")

            except KeyboardInterrupt:
                # Ctrl+C 优雅退出
                try:
                    self.io.write("Bye")
                finally:
                    break
            except Exception as exc:
                # 不崩溃：记录日志并输出错误信息后继续循环
                if self.logger:
                    self.logger.exception("REPL 循环异常：%s", exc)
                self.io.write(f"Error: {exc}")



__all__ = ["Repl"]