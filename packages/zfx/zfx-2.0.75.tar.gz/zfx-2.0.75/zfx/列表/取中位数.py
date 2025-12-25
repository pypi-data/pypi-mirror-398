from typing import Any, List, Tuple


def 取中位数(序列: List[Any]) -> Tuple[Any, bool]:
    """
    获取序列的中位数（不修改原序列）。

    功能说明:
        - 中位数是排序后的序列中处于中间位置的值。
        - 当数量为奇数时，取正中间元素。
        - 当数量为偶数时，取中间两个数的平均值。
        - 适用于数值类型的列表。

    Args:
        序列 (list): 需要计算的数值序列。

    Returns:
        tuple:
            - 任意类型: 中位数的值；失败则为 None。
            - bool: 成功返回 True，失败返回 False。

    示例:
        1) 奇数个元素：
            原序列 = [3, 1, 5]
            排序后 = [1, 3, 5]
            中位数 = 3

        2) 偶数个元素：
            原序列 = [10, 2, 4, 8]
            排序后 = [2, 4, 8, 10]
            中位数 = (4 + 8) / 2 = 6
    """
    try:
        if not 序列:
            return None, False

        排序后 = sorted(序列)
        长度 = len(排序后)
        中间 = 长度 // 2

        # 奇偶分支
        if 长度 % 2 == 1:
            return 排序后[中间], True
        else:
            return (排序后[中间 - 1] + 排序后[中间]) / 2, True

    except Exception:
        return None, False