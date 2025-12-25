import math
from typing import Iterable, SupportsFloat, Optional, List


def 求几何平均值(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列的几何平均值。

    功能说明：
        - 几何平均值适用于比率、倍数、增长率等场景。
        - 所有元素必须为正数，否则几何平均值无定义。
        - 输入为空、存在非正数或类型转换失败时返回 None。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None: 成功返回几何平均值，失败返回 None。
    """
    try:
        数列: List[float] = [float(x) for x in 数据序列]
        n = len(数列)

        if n == 0:
            return None
        if any(x <= 0 for x in 数列):
            return None

        乘积 = math.prod(数列)
        return 乘积 ** (1.0 / n)

    except Exception:
        return None
