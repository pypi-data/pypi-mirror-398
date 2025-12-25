from typing import SupportsFloat, Optional


def 求余数(被除数: SupportsFloat, 除数: SupportsFloat) -> Optional[float]:
    """
    计算两个数相除后的余数（取模运算）。

    功能说明：
        - 对输入值执行取模运算：被除数 % 除数。
        - 支持所有可转换为浮点数的输入类型，包括 int、float、可数值字符串等。
        - 若输入无法转换为数值，或除数为 0，将返回 None。
        - 返回结果为 float 类型，以确保数值类型一致。

    Args:
        被除数 (SupportsFloat): 需要取余的数值。
        除数 (SupportsFloat): 用于取模运算的除数。

    Returns:
        float | None:
            - 成功：返回余数（float）。
            - 失败：返回 None（例如除数为 0 或输入无效）。

    Notes:
        - 若需要整数取模逻辑，必须确保调用方输入整数；本函数不做额外限制。
        - Python 的取模运算对负数有特殊定义：
            a % b 的结果符号与除数一致，这是语言规范的一部分。
    """
    try:
        x = float(被除数)
        y = float(除数)
        if y == 0:
            return None
        return x % y
    except Exception:
        return None