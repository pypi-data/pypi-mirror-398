from typing import Iterable, SupportsFloat, Optional, List


def 求方差(
    数据序列: Iterable[SupportsFloat],
    *,
    样本: bool = False
) -> Optional[float]:
    """
    计算数值序列的方差。

    功能说明：
        - 支持任意可迭代数值序列。
        - 自动将所有元素转换为 float。
        - 默认计算总体方差（除以 n），若样本=True，则计算样本方差（除以 n-1）。
        - 输入为空或转换失败时返回 None。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。
        样本 (bool, optional): 是否计算样本方差（除以 n-1）。默认 False。

    Returns:
        float | None: 成功返回方差，失败返回 None。
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

        return 方差和 / (n - 1 if 样本 else n)

    except Exception:
        return None
