"""
初始化APP开发项目 ai提效工具
"""
from ylapp.core.command import Command, CommandContext
from pathlib import Path
from typing import Optional, List, Tuple
import shutil
import subprocess
import sys


class InitAiAppProjectCommand(Command):

    def __init__(self) -> None:
        super().__init__(name="initAI", description="初始化APP ai 提效工程")

    def execute(self, ctx: CommandContext) -> str:
        """
        执行以下步骤：
        1. 在当前运行目录下新建 .ylapp_spec 文件夹（存在则跳过）
        2. 进入/创建 .ylapp 目录，拉取/更新 git@coding.jd.com:capacity/collection_joycoder_rules.git
        3. 将仓库 mdc/flutter 下的所有文件拷贝到当前项目目录下的 .joycode/rules
        """
        logger = getattr(ctx, "logger", None)
        def log(info: str) -> None:
            if logger:
                logger.info(info)
            else:
                # 回显到终端（若 io 存在）
                try:
                    ctx.io.write(info + "\n")
                except Exception:
                    # 安静失败，仍返回文本
                    pass

        cwd = Path.cwd()

        # Step 1: 创建 .ylapp_spec
        spec_dir = cwd / ".ylapp_spec"
        if not spec_dir.exists():
            spec_dir.mkdir(parents=True, exist_ok=True)
            log(f"已创建目录: {spec_dir}")
        else:
            log(f"目录已存在，跳过创建: {spec_dir}")

        # Step 2: 进入/创建 .ylapp 并拉取/更新仓库
        ylapp_dir = cwd / ".ylapp"
        ylapp_dir.mkdir(parents=True, exist_ok=True)
        log(f"工作目录: {ylapp_dir}")

        repo_url = "git@coding.jd.com:capacity/collection_joycoder_rules.git"
        repo_dir = ylapp_dir / "collection_joycoder_rules"

        def run_git(args: List[str], cwd_path: Optional[Path] = None) -> Tuple[int, str, str]:
            try:
                proc = subprocess.run(
                    ["git", *args],
                    cwd=str(cwd_path) if cwd_path else None,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                return proc.returncode, proc.stdout, proc.stderr
            except FileNotFoundError:
                return 127, "", "git 未安装或不可用，请确保系统已安装 git 并配置 SSH 密钥。"

        if repo_dir.exists() and (repo_dir / ".git").exists():
            log(f"仓库已存在，执行 git pull: {repo_dir}")
            code, out, err = run_git(["pull", "--ff-only"], cwd_path=repo_dir)
            if code != 0:
                log(f"git pull 失败: {err.strip()}")
                return f"git pull 失败: {err.strip()}\n"
            else:
                log("git pull 成功")
        else:
            log(f"仓库不存在，执行 git clone 到: {repo_dir}")
            code, out, err = run_git(["clone", repo_url, str(repo_dir)])
            if code != 0:
                log(f"git clone 失败: {err.strip()}")
                return f"git clone 失败: {err.strip()}\n"
            else:
                log("git clone 成功")

        # Step 3: 拷贝 mdc/flutter -> .joycode/rules
        src_dir = repo_dir / "mdc" / "flutter"
        if not src_dir.exists():
            msg = f"源目录不存在: {src_dir}。请确认仓库结构或网络拉取是否成功。"
            log(msg)
            return msg + "\n"

        dest_dir = cwd / ".joycode" / "rules"
        dest_dir.mkdir(parents=True, exist_ok=True)
        log(f"目标目录: {dest_dir}")

        # 递归拷贝 src_dir 下所有内容到 dest_dir（保留子目录结构，覆盖同名文件）
        copied_items: List[str] = []
        for item in src_dir.iterdir():
            target = dest_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
                copied_items.append(f"{item.name}/")
            else:
                shutil.copy2(item, target)
                copied_items.append(item.name)

        summary = [
            f"操作完成：",
            f"- 已确保存在目录: {spec_dir}",
            f"- 仓库位置: {repo_dir}",
            f"- 源目录: {src_dir}",
            f"- 目标目录: {dest_dir}",
            f"- 拷贝项目数: {len(copied_items)}",
        ]
        # 附带少量清单（避免输出过长）
        preview_list = ", ".join(copied_items[:10])
        if preview_list:
            summary.append(f"- 拷贝预览(前10项): {preview_list}")

        return "\n".join(summary) + "\n"


def register(registry) -> None:
    """注册帮助命令到注册器"""
    registry.register(InitAiAppProjectCommand())


__all__ = ["InitAiAppProjectCommand", "register"]
