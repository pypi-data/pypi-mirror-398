from typing import Any, List, Tuple


def 取最小值及索引(序列: List[Any]) -> Tuple[Any, int, bool]:
    """
    获取序列中的最小值及其索引（不修改原序列）。

    功能说明:
        - 自动根据元素自身的可比较特性计算最小值。
        - 数字类型按数值大小比较。
        - 字符串类型按字符的 Unicode/ASCII 顺序比较（从首字母开始依次比较）。
        - 若最小值在序列中出现多次，则返回第一次出现的位置。
        - 原序列保持不变。

    Args:
        序列 (list): 要查找的序列。

    Returns:
        Any: 最小值；失败时为 None。
        int: 最小值的索引位置；失败时为 -1。
        bool: 是否成功；成功为 True，失败为 False。
    """
    try:
        if not 序列:
            return None, -1, False

        最小值 = min(序列)
        索引 =序列.index(最小值)
        return 最小值, 索引, True

    except Exception:
        return None, -1, False
