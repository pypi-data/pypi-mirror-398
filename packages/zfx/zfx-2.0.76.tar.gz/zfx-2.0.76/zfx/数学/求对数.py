import math
from typing import SupportsFloat, Optional


def 求对数(数值: SupportsFloat, 基数: SupportsFloat = math.e) -> Optional[float]:
    """
    计算指定数值的对数（logarithm）。

    功能说明：
        - 默认计算自然对数（以 e 为底），传入基数可计算任意底的对数。
        - 支持所有可转换为浮点数的类型，例如 int、float、可数值字符串等。
        - 若输入数值 ≤ 0、基数 ≤ 0、基数 == 1，或参数无法转换为数值，将返回 None。
        - 不抛出异常，也不打印错误信息，适合作为底层数学工具函数使用。

    Args:
        数值 (SupportsFloat): 要计算对数的数值，必须大于 0。
        基数 (SupportsFloat): 对数的底数，必须大于 0 且不能等于 1。默认使用自然对数底 e。

    Returns:
        float | None:
            - 成功：返回对数值。
            - 失败：返回 None（例如参数非法或超出数学定义域）。

    Notes:
        - math.log(x, base) 的数学定义要求：
            - x > 0
            - base > 0 且 base != 1
        - 若需高精度计算，可考虑使用 Decimal.log10 或其他高精度库。
    """
    try:
        x = float(数值)
        b = float(基数)

        if x <= 0:
            return None
        if b <= 0 or b == 1:
            return None

        return math.log(x, b)

    except Exception:
        return None
