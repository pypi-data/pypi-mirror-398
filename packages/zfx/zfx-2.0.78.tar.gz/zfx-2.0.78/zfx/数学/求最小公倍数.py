import math
from typing import SupportsInt, Optional


def 求最小公倍数(a: SupportsInt, b: SupportsInt) -> Optional[int]:
    """
    计算两个整数的最小公倍数（Least Common Multiple, LCM）。

    功能说明：
        - 使用公式 lcm(a, b) = |a * b| // gcd(a, b) 计算最小公倍数。
        - 输入将自动转换为整数；若无法转换则返回 None。
        - 若任一输入为 0，则最小公倍数为 0（符合数学定义）。
        - 本函数不抛出异常，也不打印错误信息。

    Args:
        a (SupportsInt): 第一个整数或可转换为整数的值。
        b (SupportsInt): 第二个整数或可转换为整数的值。

    Returns:
        int | None:
            - 成功：返回最小公倍数（非负整数）。
            - 失败：返回 None（如输入无法转换为整数）。

    Notes:
        - 数学性质：
            * lcm(a, 0) = 0
            * lcm(0, b) = 0
            * lcm(0, 0) = 0
        - 结果永远为非负整数，即使 a 或 b 为负数。
    """
    try:
        x = int(a)
        y = int(b)

        if x == 0 or y == 0:
            return 0

        return abs(x * y) // math.gcd(x, y)

    except Exception:
        return None
