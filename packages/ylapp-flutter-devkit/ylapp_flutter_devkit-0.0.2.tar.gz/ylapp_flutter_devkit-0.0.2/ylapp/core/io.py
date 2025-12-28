"""IO 抽象默认实现

提供 StdIO：基于标准输入输出的简单实现
- readline(prompt): 使用内置 input(prompt)
- write(text): 使用 print(text)

设计：与 ylapp.core.command.IO 协议配合使用
"""

from __future__ import annotations


class StdIO:
    """
    标准输入输出实现：
    - readline(prompt): 从终端读取一行字符串（带提示符）
    - write(text): 将文本输出到终端
    """

    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def readline(self, prompt: str) -> str:
        try:
            return input(prompt)
        except EOFError:
            # 输入流结束时返回空字符串，交由调用方决定是否退出循环
            return ""

    def write(self, text: str) -> None:
        print(text)


__all__ = ["StdIO"]