import math
from typing import Iterable, SupportsFloat, Optional, List


def 求标准差(
    数据序列: Iterable[SupportsFloat],
    *,
    样本: bool = False
) -> Optional[float]:
    """
    计算数值序列的标准差。

    功能说明：
        - 支持所有可迭代的数值序列：list、tuple、set、生成器等。
        - 序列中的每个元素将自动转换为 float。
        - 默认计算“总体标准差”（Population Standard Deviation）。
        - 若参数 `样本=True`，则计算“样本标准差”（Sample Standard Deviation）。
        - 输入为空或转换失败时返回 None，不抛异常、不打印错误。

    Args:
        数据序列 (Iterable[SupportsFloat]):
            任意可迭代的数值序列。
        样本 (bool, optional):
            是否计算样本标准差（默认 False）。
            - False：总体标准差（除以 n）
            - True：样本标准差（除以 n - 1）

    Returns:
        float | None:
            - 成功：返回标准差（float）
            - 失败：返回 None

    Notes:
        - 总体标准差公式：
              sqrt( Σ(x - μ)² / n )
        - 样本标准差公式：
              sqrt( Σ(x - x̄)² / (n - 1) )
        - 样本标准差至少需要 2 个数据点，否则返回 None。
    """
    try:
        数列: List[float] = [float(x) for x in 数据序列]
        n = len(数列)

        if n == 0:
            return None
        if 样本 and n < 2:
            return None

        平均值 = sum(数列) / n

        方差和 = sum((x - 平均值) ** 2 for x in 数列)

        if 样本:
            方差 = 方差和 / (n - 1)
        else:
            方差 = 方差和 / n

        return math.sqrt(方差)

    except Exception:
        return None
