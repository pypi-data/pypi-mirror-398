from typing import Any, List, Tuple


def 差集(序列1: List[Any], 序列2: List[Any]) -> Tuple[List[Any], bool]:
    """
    获取两个序列的差集（序列1 - 序列2，顺序稳定）。

    功能说明:
        - 返回仅存在于序列1，且不在序列2中的元素。
        - 顺序保持与序列1一致。
        - 不修改原序列。

    Args:
        序列1 (list): 基础序列。
        序列2 (list): 需要排除的序列。

    Returns:
        tuple:
            - list: 差集后的新序列。失败则为空列表。
            - bool: 成功返回 True，失败返回 False。
    """
    try:
        排除 = set(序列2)
        结果 = [元素 for 元素 in 序列1 if 元素 not in 排除]
        return 结果, True
    except Exception:
        return [], False
