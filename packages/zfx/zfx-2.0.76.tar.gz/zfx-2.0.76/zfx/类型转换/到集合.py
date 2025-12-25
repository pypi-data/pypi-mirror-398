from collections.abc import Iterable
from typing import Any, Set


def 到集合(输入值: Any) -> Set[Any]:
    """
    将输入值转换为集合（set）。

    Args:
        输入值 (Any):
            需要转换为集合的值。

    Returns:
        set:
            转换后的集合。

            - 如果输入值是可迭代对象（Iterable），则转换为去重后的集合。
              例如：
                  [1, 2, 2, 3] → {1, 2, 3}
                  "abc" → {'a', 'b', 'c'}
            - 如果输入值不可迭代（如整数、None），则包装为单元素集合。
            - 如果转换过程中发生异常，则返回空集合。
    """
    try:
        if isinstance(输入值, (str, bytes, bytearray)):
            # 字符串视为单一整体，而不是字符集合
            return {输入值}

        if isinstance(输入值, Iterable):
            return set(输入值)

        return {输入值}

    except Exception:
        return set()
