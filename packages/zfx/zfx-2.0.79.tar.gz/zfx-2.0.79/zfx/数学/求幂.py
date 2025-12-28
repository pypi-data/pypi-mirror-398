import math
from typing import SupportsFloat, Optional


def 求幂(基数: SupportsFloat, 指数: SupportsFloat) -> Optional[float]:
    """
    计算数值的幂（基数 ** 指数）。

    功能说明：
        - 使用 math.pow 执行幂运算，返回浮点数结果。
        - 支持所有可转换为 float 的类型作为输入，例如 int、float、可数值字符串等。
        - 若输入无法转换为数值，或数学上不支持（例如负底数开非整数次方），将返回 None。
        - 本函数不抛出异常，也不打印错误信息，适合作为底层数学工具函数使用。

    Args:
        基数 (SupportsFloat): 幂运算的底数。
        指数 (SupportsFloat): 幂运算的指数。

    Returns:
        float | None:
            - 成功：返回幂运算后的浮点值。
            - 失败：返回 None（如输入非法或结果为数学上未定义的值）。

    Notes:
        - math.pow 与内置运算符 ** 的差异：
            * math.pow 始终返回 float。
            * ** 若输入是 int，可能返回 int（例如 2**3 = 8）。
        - Python 的 math.pow 不支持复数运算，例如 (-1) ** 0.5 会报 ValueError。
    """
    try:
        x = float(基数)
        y = float(指数)
        return math.pow(x, y)
    except Exception:
        return None
