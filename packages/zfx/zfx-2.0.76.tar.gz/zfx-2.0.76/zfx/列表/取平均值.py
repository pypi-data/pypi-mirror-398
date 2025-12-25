from typing import Any, List


def 取平均值(序列: List[Any]) -> float:
    """
    计算序列中所有数字元素的平均值。

    功能说明:
        - 仅当序列非空，且所有元素为数字（int 或 float）时才计算平均值。
        - 如果序列为空、包含非数字元素或出现异常，则返回 -1。
        - 不修改原序列。

    Args:
        序列 (list): 包含数字的列表。

    Returns:
        float: 序列中所有数字的平均值；若无法计算或异常，则返回 -1。
    """
    try:
        if not 序列:
            return -1

        # 确保所有元素都是数字
        for 元素 in 序列:
            if not isinstance(元素, (int, float)):
                return -1

        return sum(序列) / len(序列)
    except Exception:
        return -1
