from typing import Any, List


def 取成员索引(序列: List[Any], 目标成员: Any) -> int:
    """
    获取目标成员在序列中首次出现的索引。

    功能说明:
        - 使用序列的 index 方法查找目标成员的位置。
        - 如果目标成员不存在，返回 -1。
        - 如果出现异常（如序列不是可索引对象），返回 -1。

    Args:
        序列 (list): 包含元素的列表。
        目标成员 (any): 要查找的成员。

    Returns:
        int: 目标成员的索引位置；如果不存在或发生异常，返回 -1。
    """
    try:
        return 序列.index(目标成员)
    except ValueError:
        return -1
    except Exception:
        return -1
