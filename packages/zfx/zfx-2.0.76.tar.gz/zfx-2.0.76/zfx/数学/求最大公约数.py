import math
from typing import SupportsInt, Optional


def 求最大公约数(a: SupportsInt, b: SupportsInt) -> Optional[int]:
    """
    计算两个整数的最大公约数（Greatest Common Divisor, GCD）。

    功能说明：
        - 使用 math.gcd 计算最大公约数。
        - 输入值将被转换为 int；若无法转换为整数，将返回 None。
        - 对负数的处理遵循数学规范：gcd(a, b) 的结果总是非负整数。
        - 若 a 与 b 全为 0，则 math.gcd(0, 0) 返回 0。

    Args:
        a (SupportsInt): 第一个整数或可转换为整数的值。
        b (SupportsInt): 第二个整数或可转换为整数的值。

    Returns:
        int | None:
            - 成功：返回最大公约数（非负整数）。
            - 失败：返回 None（例如输入类型非法）。

    Notes:
        - gcd 的数学性质：
            * gcd(a, 0) = |a|
            * gcd(0, b) = |b|
            * gcd(0, 0) = 0
        - 本函数不处理多数字 GCD（如 gcd(a, b, c…)），若需要可进一步扩展。
    """
    try:
        x = int(a)
        y = int(b)
        return math.gcd(x, y)
    except Exception:
        return None
