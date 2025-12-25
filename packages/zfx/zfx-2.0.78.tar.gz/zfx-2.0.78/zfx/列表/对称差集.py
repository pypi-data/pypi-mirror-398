from typing import Any, List, Tuple


def 对称差集(序列1: List[Any], 序列2: List[Any]) -> Tuple[List[Any], bool]:
    """
    获取两个序列的对称差集（顺序稳定）。

    功能说明:
        - 返回只出现在任意一个序列中、但不能同时出现于两个序列的元素。
        - 顺序保持：先序列1的顺序，再序列2的顺序。
        - 不修改原序列。

    Args:
        序列1 (list): 第一个序列。
        序列2 (list): 第二个序列。

    Returns:
        tuple:
            - list: 对称差集的新序列；失败则为空列表。
            - bool: 成功返回 True，失败返回 False。
    """
    try:
        集合1 = set(序列1)
        集合2 = set(序列2)

        # 对称差 = (只在序列1中) + (只在序列2中)
        结果 = []

        for 元素 in 序列1:
            if 元素 not in 集合2:
                结果.append(元素)

        for 元素 in 序列2:
            if 元素 not in 集合1:
                结果.append(元素)

        return 结果, True
    except Exception:
        return [], False