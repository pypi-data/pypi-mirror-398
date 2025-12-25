import math
from typing import Iterable, SupportsFloat, Optional, List


def 求积(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列中所有元素的乘积。

    功能说明：
        - 支持任意可迭代的数值序列。
        - 自动将每个元素转换为 float。
        - 输入为空或转换失败时返回 None。
        - 使用 math.prod 执行高效乘积运算。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None: 成功返回乘积，失败返回 None。
    """
    try:
        数列: List[float] = [float(x) for x in 数据序列]
        if not 数列:
            return None
        return math.prod(数列)
    except Exception:
        return None
