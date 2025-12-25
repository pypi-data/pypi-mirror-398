from collections.abc import Iterable
from typing import Any, List


def 到列表(输入值: Any) -> List[Any]:
    """
    将输入值转换为列表（数组）。

    Args:
        输入值 (Any):
            需要转换为列表的值。

    Returns:
        list:
            转换后的列表。

            - 如果输入值是可迭代对象（Iterable），则展开为列表。
              可迭代对象指可以被 `for` 循环遍历的对象，如：
              列表（list）、元组（tuple）、集合（set）、字典（dict）、range(10) 等。
              但字符串、字节、字节数组虽然 technically 可迭代，但此处视为单个值处理。
            - 如果输入值不可迭代（如整数、浮点数、None 等），则包装为单元素列表。
            - 如果发生异常，则返回空列表。
    """
    try:
        # 字符串、字节类型不视为可迭代容器
        if isinstance(输入值, (str, bytes, bytearray)):
            return [输入值]

        # 可迭代对象直接转换
        if isinstance(输入值, Iterable):
            return list(输入值)

        # 不可迭代对象包装为单元素列表
        return [输入值]

    except Exception:
        return []
