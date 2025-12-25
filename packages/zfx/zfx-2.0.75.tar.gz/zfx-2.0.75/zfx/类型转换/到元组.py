from collections.abc import Iterable
from typing import Any, Tuple


def 到元组(输入值: Any) -> Tuple[Any, ...]:
    """
    将输入值转换为元组（tuple）。

    Args:
        输入值 (Any):
            需要转换为元组的值。

    Returns:
        tuple:
            转换后的元组。

            - 如果输入值是可迭代对象（Iterable），则展开为元组。
              可迭代对象指可以被 `for` 循环遍历的对象，如：
              列表（list）、元组（tuple）、集合（set）、字典（dict）、range(10) 等。
              但字符串、字节、字节数组虽然 technically 可迭代，但此处视为单个值处理。
            - 如果输入值不可迭代（如整数、浮点数、None 等），则包装为单元素元组。
            - 如果转换失败或出现异常，则返回空元组 ()。
    """
    try:
        # 字符串、字节类型不视为可迭代容器
        if isinstance(输入值, (str, bytes, bytearray)):
            return (输入值,)

        # 可迭代对象直接转换
        if isinstance(输入值, Iterable):
            return tuple(输入值)

        # 不可迭代对象包装成单元素元组
        return (输入值,)

    except Exception:
        return ()
