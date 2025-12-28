"""g.dart 生成文件扫描命令

功能：
- 递归扫描指定目录下的 *.g.dart 自动生成文件
- 提取 `part of 'xxx.dart';` 主文件引用并校验主文件是否存在
- 对比主文件字段并输出汇总统计与明细列表（额外字段、解析异常等信息）

用法（REPL 内）：
/gdtoScan [path]
- path 可选，默认为当前工作目录 "."
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

from ylapp.core.command import Command, CommandContext

# `_PART_OF_RE`：捕获 g.dart 头部的 `part of 'xxx.dart';`，用于定位主文件名
_PART_OF_RE = re.compile(r"""part\s+of\s+['"]([^'"]+)['"];""", re.IGNORECASE)
# `_GENERATED_HINT_RE`：检测生成文件标记，便于输出“标记:生成文件/未知”
_GENERATED_HINT_RE = re.compile(r"GENERATED CODE - DO NOT MODIFY BY HAND", re.IGNORECASE)
# `_G_MAP_KEY_RE`：匹配序列化 map 中的键名（形如 "field": ...）
_G_MAP_KEY_RE = re.compile(r"""['"]([A-Za-z_]\w*)['"]\s*:""")
# `_G_JSON_ACCESS_RE`：匹配 `json['field']` 访问的字段名
_G_JSON_ACCESS_RE = re.compile(r"""json\[['"]([A-Za-z_]\w*)['"]\]""")
# `_FIELD_DECL_RE`：在主文件内匹配字段声明，捕获修饰符以支持过滤 static
_FIELD_DECL_RE = re.compile(
    r"""^[ \t]*((?:(?:static|final|const|late)\s+)*)[\w<>\?\[\],\.]+\s+([A-Za-z_]\w*)\s*(?:[;=])""",
    re.MULTILINE,
)


def _strip_comments(content: str) -> str:
    """移除多行与单行注释，避免注释内的关键字误判为字段。"""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
    content = re.sub(r"//.*", "", content)
    return content


def _extract_main_fields(main_content: str) -> Optional[Set[str]]:
    """从主文件中提取字段声明集合；解析失败返回 None 以触发上层的“字段解析失败”提示。"""
    try:
        cleaned = _strip_comments(main_content)
        fields: Set[str] = set()
        for line in cleaned.splitlines():
            line = line.strip()
            if not line or "(" in line:  # 跳过方法/构造函数等含括号的行
                continue
            match = _FIELD_DECL_RE.match(line)
            if match:
                modifiers = match.group(1) or ""
                field_name = match.group(2)
                # 过滤 static 字段和私有字段
                if "static" in modifiers:
                    continue
                if field_name.startswith("_"):
                    continue
                fields.add(field_name)
        return fields
    except Exception:
        return None


def _extract_g_fields(g_content: str) -> Optional[Set[str]]:
    """从生成文件中提取字段名（map 键 + json 下标访问）；异常时返回 None 供上层判定解析失败。"""
    try:
        cleaned = _strip_comments(g_content)
        fields: Set[str] = set(_G_MAP_KEY_RE.findall(cleaned))
        fields.update(_G_JSON_ACCESS_RE.findall(cleaned))
        return fields
    except Exception:
        return None


def _read_head(file_path: Path, max_bytes: int = 4096) -> str:
    """仅读取文件头部，减少 I/O 开销；失败时返回空字符串以保持后续流程安全。"""
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except Exception:
        return ""


def _probe_g_file(file_path: Path) -> Tuple[Optional[str], bool, bool]:
    """读取 g.dart 头部获取 (part_of 路径, 是否含生成标记, 主文件是否存在)。"""
    head = _read_head(file_path)
    part_match = _PART_OF_RE.search(head)
    part_of = part_match.group(1) if part_match else None
    has_generated_hint = bool(_GENERATED_HINT_RE.search(head))
    if part_of:
        main_path = file_path.parent / part_of
        main_exists = main_path.exists()
    else:
        main_exists = False
    return part_of, has_generated_hint, main_exists


class GdtoScanCommand(Command):
    """扫描 Flutter g.dart 生成文件"""

    def __init__(self) -> None:
        super().__init__(name="dtoScan", description="扫描 *.g.dart 自动生成文件并校验主文件存在性")

    def execute(self, ctx: CommandContext) -> str:
        """执行流程：
        1) 读取路径参数（默认当前目录），校验存在性与目录属性。
        2) 递归收集 *.g.dart 文件，统计总数。
        3) 逐文件检查：
           - part 声明与主文件存在性
           - 生成文件标记
           - 若主文件存在，解析主/生成字段并计算 extra_fields（g.dart 中多出的字段）。
           - 解析异常时标记 “字段解析失败”，并保持功能输出稳定。
        4) 汇总额外字段文件数量(extra_fields_count)与明细。
        """
        # 获取命令行参数作为扫描根目录，默认为当前目录
        args: List[str] = ctx.args or []
        root_arg = args[0] if args else "."
        # 解析绝对路径
        root = Path(root_arg).expanduser().resolve()

        # 校验目录是否存在
        if not root.exists():
            return f"路径不存在：{root}"
        if not root.is_dir():
            return f"路径不是目录：{root}"

        # 递归搜索所有 .g.dart 结尾的文件
        g_files: List[Path] = [p for p in root.rglob("*.g.dart") if p.is_file()]

        extra_fields_count = 0  # 统计含有额外字段的 g.dart 文件数量
        missing_fields_count = 0  # 统计含有缺失字段的主文件数量
        # 初始化输出信息头部
        lines: List[str] = [
            f"扫描目录：{root}",
            f"发现 g.dart 文件：{len(g_files)}",
        ]
        # 如果没有发现文件，直接返回
        if not g_files:
            return "\n".join(lines)

        # 添加表格头
        lines.append("明细：路径 | 状态 | extra_fields | missing_fields")
        # 遍历所有发现的文件（按路径排序）
        for g_file in sorted(g_files):
            # 探测文件元数据：所属主文件、是否有生成标记、主文件是否存在
            part_of, has_generated_hint, main_exists = _probe_g_file(g_file)
            rel_path = g_file.relative_to(root)
            status_parts: List[str] = []
            
            # 构建状态描述：part 声明
            if part_of:
                status_parts.append(f"part of {part_of}")
            else:
                status_parts.append("part 声明缺失")
            # 构建状态描述：生成标记和主文件状态
            status_parts.append("标记:生成文件" if has_generated_hint else "标记:未知")
            status_parts.append("主文件存在" if main_exists else "主文件缺失")

            # 检查额外字段与缺失字段
            extra_fields_display = "-"
            missing_fields_display = "-"
            parse_failed = False
            # 只有当关联的主文件存在时才进行字段对比
            if part_of and main_exists:
                main_path = g_file.parent / part_of
                try:
                    # 读取文件内容，忽略编码错误
                    g_content = g_file.read_text(encoding="utf-8", errors="ignore")
                    main_content = main_path.read_text(encoding="utf-8", errors="ignore")
                    
                    # 提取字段集合
                    main_fields = _extract_main_fields(main_content)
                    g_fields = _extract_g_fields(g_content)
                    
                    if main_fields is None or g_fields is None:
                        parse_failed = True
                    else:
                        # 计算差集：在 g.dart 中存在但在主文件中不存在的字段 (Extra)
                        extra_fields = sorted(g_fields - main_fields)
                        if extra_fields:
                            extra_fields_display = ",".join(extra_fields)
                            extra_fields_count += 1
                        
                        # 计算差集：在主文件中存在但在 g.dart 中不存在的字段 (Missing)
                        missing_fields = sorted(main_fields - g_fields)
                        if missing_fields:
                            missing_fields_display = ",".join(missing_fields)
                            missing_fields_count += 1
                except Exception:
                    # 任意读取/解析异常都记为解析失败，保持程序不中断
                    parse_failed = True
                
                if parse_failed:
                    extra_fields_display = "字段解析失败"
                    missing_fields_display = "字段解析失败"
            
            # 添加单行文件状态信息
            if extra_fields_display != "-" or missing_fields_display != "-":
                # 如果有差异，使用更显眼的标记
                line_content = f"!!! {rel_path} | " + " | ".join(status_parts) + f" | {extra_fields_display} | {missing_fields_display}"
            else:
                line_content = f"- {rel_path} | " + " | ".join(status_parts) + f" | {extra_fields_display} | {missing_fields_display}"
            lines.append(line_content)

        # 汇总：差异统计置于总览部分
        if extra_fields_count > 0 or missing_fields_count > 0:
            summary = (
                f"\n{'=' * 60}\n"
                f"⚠️  警告：发现字段不一致！\n"
                f"   额外字段文件数：{extra_fields_count}\n"
                f"   缺失字段文件数：{missing_fields_count}\n"
                f"{'=' * 60}"
            )
        else:
            summary = f"额外字段文件数：{extra_fields_count}，缺失字段文件数：{missing_fields_count}"
            
        lines.insert(2, summary)
        return "\n".join(lines)


def register(registry) -> None:
    """注册 g.dart 扫描命令"""
    registry.register(GdtoScanCommand())