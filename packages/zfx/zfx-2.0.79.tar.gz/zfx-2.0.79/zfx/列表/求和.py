from typing import Any, List, Tuple


def 求和(序列: List[Any]) -> Tuple[float, bool]:
    """
    求序列中所有数字元素的总和。

    功能说明:
        - 所有元素必须为数字类型（int 或 float）。
        - 成功返回 (总和, True)，失败返回 (-1, False)。

    Args:
        序列 (list): 包含数字的序列。

    Returns:
        tuple:
            - 总和 (float): 序列中元素的和；失败时为 -1。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        for 元素 in 序列:
            if not isinstance(元素, (int, float)):
                return -1, False

        return sum(序列), True
    except Exception:
        return -1, False
