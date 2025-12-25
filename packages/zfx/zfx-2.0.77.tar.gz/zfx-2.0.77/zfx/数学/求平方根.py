import math
from typing import SupportsFloat, Optional


def 求平方根(数值: SupportsFloat) -> Optional[float]:
    """
    计算数值的平方根。

    功能说明：
        - 使用 math.sqrt 计算平方根。
        - 支持所有可转换为 float 的输入类型（如 int、float、可数值字符串等）。
        - 若输入为负数，或无法转换为浮点数，则返回 None。
        - 本函数不抛出异常，也不打印错误信息，适合作为底层数学工具函数使用。

    Args:
        数值 (SupportsFloat): 需要计算平方根的数值，必须为非负数。

    Returns:
        float | None:
            - 成功：返回平方根（float 类型）。
            - 失败：返回 None（如输入非法或数值为负数）。

    Notes:
        - math.sqrt 对负数会报 ValueError，本函数将返回 None 而不是抛异常。
        - 若需要计算复数平方根，应使用 cmath.sqrt()，本函数不处理复数运算。
    """
    try:
        x = float(数值)
        if x < 0:
            return None
        return math.sqrt(x)
    except Exception:
        return None
