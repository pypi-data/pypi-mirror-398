import math
from typing import SupportsFloat, Optional


def 求阶乘(数值: SupportsFloat) -> Optional[int]:
    """
    计算非负整数的阶乘。

    功能说明：
        - 支持可转换为整数的输入类型，如 int、float(整数值)、可数值字符串等。
        - 若输入为小数、负数或无法转换为整数，返回 None。
        - 使用 math.factorial 计算阶乘，结果始终为 int。
        - 本函数不抛出异常，也不打印错误日志，适合作为底层数学工具函数。

    Args:
        数值 (SupportsFloat): 需要计算阶乘的数值，必须为非负整数。

    Returns:
        int | None:
            - 成功：返回阶乘结果。
            - 失败：返回 None（输入非法，如负数或非整数）。

    Notes:
        - 隐式整数转换规则：
            * 5.0 会被视为有效整数
            * 5.3 不会被视为整数，将返回 None
        - 阶乘增长速度极快，大整数运算可能消耗较多计算资源。
    """
    try:
        # 尝试转换为浮点数
        x = float(数值)

        # 必须是整数形式
        if not x.is_integer():
            return None

        n = int(x)

        if n < 0:
            return None

        return math.factorial(n)

    except Exception:
        return None
