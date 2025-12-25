from typing import Any, List


def 取元素出现次数(序列: List[Any], 目标元素: Any) -> int:
    """
    统计目标元素在序列中出现的次数。

    功能说明:
        - 遍历序列，统计所有等于目标元素的元素数量。
        - 如果出现异常（如序列不可迭代），返回 -1，便于调用方区分错误与真实计数。

    Args:
        序列 (list): 包含元素的列表。
        目标元素 (any): 要统计出现次数的目标元素。

    Returns:
        int: 目标元素出现的次数；如果出现异常，返回 -1。
    """
    try:
        计数 = 0
        for 元素 in 序列:
            if 元素 == 目标元素:
                计数 += 1
        return 计数
    except Exception:
        return -1
