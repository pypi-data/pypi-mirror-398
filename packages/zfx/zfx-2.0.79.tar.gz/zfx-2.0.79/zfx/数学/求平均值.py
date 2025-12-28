from typing import Iterable, SupportsFloat, Optional


def 求平均值(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列的算术平均值。

    功能说明：
        - 支持任意可迭代的数值序列，如 list、tuple、set、生成器等。
        - 所有元素将尝试转换为 float；若有元素无法转换，将返回 None。
        - 序列为空时返回 None，不抛出异常。
        - 不打印错误信息，适合作为底层数学工具函数使用。
        - 返回 float 类型结果，确保类型一致性。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None:
            - 成功：返回平均值（float）。
            - 失败：返回 None（如输入不可转换或序列为空）。

    Notes:
        - 若需要加权平均，可在此基础上扩展。
        - 若需要高精度平均值，可结合 Decimal 使用。
    """
    try:
        数列 = [float(x) for x in 数据序列]

        if not 数列:
            return None

        return float(sum(数列) / len(数列))

    except Exception:
        return None
