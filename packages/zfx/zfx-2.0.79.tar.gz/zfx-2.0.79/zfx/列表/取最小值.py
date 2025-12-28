from typing import Any, List, Tuple


def 取最小值(序列: List[Any]) -> Tuple[float, bool]:
    """
    获取序列中的最小值。

    功能说明:
        - 序列必须非空。
        - 所有元素必须为数字类型（int 或 float）。
        - 函数不会修改原序列。
        - 成功返回 (最小值, True)，失败返回 (-1, False)。

    Args:
        序列 (list): 包含数字的序列。

    Returns:
        tuple:
            - 最小值 (float): 若失败则为 -1。
            - 是否成功 (bool): 成功为 True；失败为 False。
    """
    try:
        if not 序列:
            return -1, False

        for 元素 in 序列:
            if not isinstance(元素, (int, float)):
                return -1, False

        return min(序列), True
    except Exception:
        return -1, False