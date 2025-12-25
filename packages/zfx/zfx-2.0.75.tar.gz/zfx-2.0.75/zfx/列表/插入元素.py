from typing import Any, List, Tuple


def 插入元素(序列: List[Any], 位置: int, 元素: Any) -> Tuple[List[Any], bool]:
    """
    在指定位置插入一个元素并返回新序列。

    功能说明:
        - 不修改原序列。
        - 若位置越界，将在序列尾部插入。
        - 成功返回 (新序列, True)，失败返回 ([], False)。

    Args:
        序列 (list): 原始序列。
        位置 (int): 插入位置索引。
        元素 (any): 要插入的元素。

    Returns:
        tuple:
            - 新序列 (list): 插入后的序列；失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        新序列 = 序列.copy()

        if 位置 < 0:
            位置 = 0
        elif 位置 > len(新序列):
            位置 = len(新序列)

        新序列.insert(位置, 元素)
        return 新序列, True
    except Exception:
        return [], False
