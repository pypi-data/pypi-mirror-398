from typing import Iterable, SupportsFloat, Optional, List


def 求调和平均值(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列的调和平均值。

    功能说明：
        - 调和平均适用于速率、单位价格等“倒数平均”场景。
        - 序列中的数值必须全部为正数。
        - 输入为空、存在非正数或转换失败时返回 None。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None: 成功返回调和平均值，失败返回 None。
    """
    try:
        数列: List[float] = [float(x) for x in 数据序列]
        n = len(数列)

        if n == 0:
            return None
        if any(x <= 0 for x in 数列):
            return None

        倒数和 = sum(1.0 / x for x in 数列)
        return n / 倒数和

    except Exception:
        return None
