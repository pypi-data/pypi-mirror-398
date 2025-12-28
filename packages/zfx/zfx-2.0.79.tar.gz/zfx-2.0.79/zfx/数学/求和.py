from typing import Iterable, SupportsFloat, Optional


def 求和(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列的总和。

    功能说明：
        - 支持所有可迭代的数据类型，例如 list、tuple、set、生成器等。
        - 序列中的每个元素将被转换为 float 后再参与求和运算。
        - 若序列为空或有元素无法转换为数值，则返回 None。
        - 本函数不抛出异常，也不打印错误日志，适合作为底层数学工具函数使用。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None:
            - 成功：返回所有数值相加后的总和（float）。
            - 失败：返回 None（例如类型非法或转换失败）。

    Notes:
        - 若需要高精度求和（如金融领域），请使用 Decimal 累加以避免浮点误差。
        - 本函数不修改传入序列，不会产生副作用。
    """
    try:
        数列 = [float(x) for x in 数据序列]
        if not 数列:
            return None
        return float(sum(数列))
    except Exception:
        return None
