from typing import Iterable, SupportsFloat, Optional, List


def 求中位数(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列的中位数。

    功能说明：
        - 支持所有可迭代且其元素可转换为浮点数的序列（如 list、tuple、set、生成器等）。
        - 自动将序列中的每个元素转换为 float 类型。
        - 不会修改调用方传入的原始序列（内部会创建副本）。
        - 空序列返回 None，不抛出异常。
        - 对偶数个元素的序列，采用“两中间值均值法”，符合统计学标准定义。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None:
            - 成功时返回计算出的中位数。
            - 序列为空或元素无法转换为数值时返回 None。

    Notes:
        - 本函数不依赖第三方库。
        - 若序列非常大，可考虑使用分区选择算法以提高性能（本实现专注稳定性与可读性）。
    """
    try:
        数列: List[float] = [float(x) for x in 数据序列]

        if not 数列:
            return None

        数列.sort()
        n = len(数列)
        mid = n // 2

        if n % 2 == 0:
            return (数列[mid - 1] + 数列[mid]) / 2
        else:
            return 数列[mid]

    except Exception:
        return None
