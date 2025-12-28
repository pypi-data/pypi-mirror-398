import typer

from ylapp import __version__
from ylapp.core.io import StdIO
from ylapp.core.config import load_config
from ylapp.core.logger import configure_logging, get_logger
from ylapp.core.registry import CommandRegistry
from ylapp.core.router import Router
from ylapp.core.repl import Repl
from ylapp.commands import help as help_cmd
from ylapp.commands.dto_scan import gdto_scan
from ylapp.commands import init_ai_app_project as init_ai_app_project_cmd

# 顶层 CLI 应用
cli = typer.Typer(add_completion=False, help="ylapp 命令行工具")

# app 子命令作为子 Typer，进入 REPL
app_typer = typer.Typer(help="进入交互式 REPL", invoke_without_command=True)


@app_typer.callback()
def app_callback() -> None:
    """
    app 子命令入口：
    - 初始化 Config 与 Logger
    - 注册内置命令（/h）
    - 启动 REPL 主循环
    """
    # 加载配置与初始化日志
    config = load_config()
    configure_logging(config.log_level)
    logger = get_logger("ylapp.cli")

    # 初始化 IO/Registry/Router
    io = StdIO()
    registry = CommandRegistry(logger=logger)
    router = Router(logger=logger)

    # 注册内置命令
    help_cmd.register(registry)
    init_ai_app_project_cmd.register(registry)
    gdto_scan.register(registry)

    # 欢迎横幅包含版本号
    config.banner = f"ylapp CLI v{__version__} (输入 /help 查看命令)"

    # 启动 REPL
    repl = Repl(io=io, router=router, registry=registry, config=config, logger=logger)
    repl.run()


# 挂载子命令：支持 `python -m ylapp.cli app`
cli.add_typer(app_typer, name="app")


def main() -> None:
    """
    CLI 入口函数：
    - 当前可通过 `python -m ylapp.cli app` 进入 REPL
    - 后续将通过 console_scripts 暴露系统命令 `ylapp`（见打包任务）
    """
    cli()


if __name__ == "__main__":
    main()