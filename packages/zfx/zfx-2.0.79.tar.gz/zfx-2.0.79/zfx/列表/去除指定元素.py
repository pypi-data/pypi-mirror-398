from typing import Any, List


def 去除指定元素(序列: List[Any], 目标元素: Any) -> List[Any]:
    """
    返回移除指定元素后的新列表。

    功能说明:
        - 移除与目标元素相等的所有元素。
        - 不修改原序列，返回新的列表。
        - 如果出现异常，返回空列表。

    Args:
        序列 (list): 原始列表。
        目标元素 (any): 要移除的元素。

    Returns:
        list: 去除指定元素后的列表。如果出现异常，返回空列表。
    """
    try:
        return [x for x in 序列 if x != 目标元素]
    except Exception:
        return []
