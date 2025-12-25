from typing import Any, List


def 反转(序列: List[Any]) -> List[Any]:
    """
    反转序列中的元素顺序。

    功能说明:
        - 使用切片操作实现反转，不修改原序列。
        - 如果出现异常，返回空列表。

    Args:
        序列 (list): 要反转的列表。

    Returns:
        list: 反转后的新列表。如果出现异常，返回空列表。
    """
    try:
        return 序列[::-1]
    except Exception:
        return []