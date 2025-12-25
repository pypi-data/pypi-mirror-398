from typing import Any, List


def 去除空元素(序列: List[Any]) -> List[Any]:
    """
    去除序列中的空元素。

    功能说明:
        - 移除所有在布尔上下文中为 False 的元素（如空字符串、0、None、空列表等）。
        - 不修改原序列。
        - 如果出现异常，返回空列表。

    Args:
        序列 (list): 要处理的列表。

    Returns:
        list: 去除空元素后的新列表。如果出现异常，返回空列表。
    """
    try:
        return [x for x in 序列 if x]
    except Exception:
        return []
