"""
工具函数模块
提供常用的辅助函数，如 Excel 列索引转换、文本处理等
"""

import re
from collections import defaultdict
from typing import overload, Optional

# 简单检测"中文"的正则（CJK统一表意文字）
CJK = re.compile(r"[\u4e00-\u9fff]")

# 匹配一对中/英文括号内的内容（不跨越嵌套）
PAT = re.compile(r"[（(]([^（）()]*)[）)]")


@overload
def xls(col_or_start: int, end: None = None) -> int: ...
@overload
def xls(col_or_start: int, end: int) -> slice: ...


def xls(col_or_start: int, end: Optional[int] = None):
    """
    将 Excel 列索引（从1开始）转换为 Python 索引（从0开始）

    这个函数用于在 Python 中方便地使用 Excel 的列号（从1开始）来索引数据。

    Args:
        col_or_start: Excel 列号（从1开始），或范围的起始列号
        end: 可选，范围的结束列号（从1开始）

    Returns:
        如果只提供 col_or_start，返回 Python 索引（col_or_start - 1）
        如果提供了 end，返回 slice 对象（从 col_or_start-1 到 end）

    Examples:
        >>> # 获取第1列（Excel列号）的 Python 索引
        >>> xls(1)
        0

        >>> # 获取第2到第5列（Excel列号）的切片
        >>> xls(2, 5)
        slice(1, 5, None)

        >>> # 在列表中使用
        >>> data = ['a', 'b', 'c', 'd', 'e']
        >>> data[xls(1)]  # 获取第1列
        'a'
        >>> data[xls(2, 4)]  # 获取第2到第4列
        ['b', 'c', 'd']
    """
    if end is None:
        return col_or_start - 1
    return slice(col_or_start - 1, end)


def fix_parens(text: str) -> str:
    """
    修复文本中的括号，保证中英文括号成对出现

    如果括号内的内容包含中文，使用中文括号；否则使用英文括号。
    反复替换直到不再变化，以应对一段文字中多处括号的情况。

    Args:
        text: 需要处理的文本字符串

    Returns:
        处理后的文本字符串，括号已统一

    Examples:
        >>> fix_parens("测试(中文)")
        '测试（中文）'
        >>> fix_parens("测试(English)")
        '测试(English)'
        >>> fix_parens("测试(中文)和(English)")
        '测试（中文）和(English)'
    """

    def _repl(m: re.Match) -> str:
        inner = m.group(1)
        return f"（{inner}）" if CJK.search(inner) else f"({inner})"

    # 反复替换直到不再变化（应对一段文字中多处括号）
    prev = None
    while prev != text:
        prev = text
        text = PAT.sub(_repl, text)
    return text


def make_unique(names: list, sep: str = "_") -> list:
    """
    确保列表中的名称唯一，重复的名称会添加序号后缀

    Args:
        names: 需要处理的名称列表
        sep: 分隔符，用于连接原名称和序号（默认为 "_"）

    Returns:
        处理后的名称列表，所有名称都是唯一的

    Examples:
        >>> make_unique(['a', 'b', 'a', 'c', 'b'])
        ['a', 'b', 'a_2', 'c', 'b_2']
        >>> make_unique(['test', 'test', 'test'], sep='-')
        ['test', 'test-2', 'test-3']
    """
    counter = defaultdict(int)
    result = []

    for name in names:
        counter[name] += 1
        if counter[name] == 1:
            result.append(name)
        else:
            result.append(f"{name}{sep}{counter[name]}")
    return result
