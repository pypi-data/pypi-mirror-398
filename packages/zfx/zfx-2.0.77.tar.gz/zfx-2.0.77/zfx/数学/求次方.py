from typing import SupportsFloat, Optional


def 求次方(基数: SupportsFloat, 指数: SupportsFloat) -> Optional[float]:
    """
    计算基数的指定次方（base ** exponent）。

    功能说明：
        - 执行幂运算：基数 ** 指数。
        - 支持所有可转换为 float 的类型，例如 int、float、可数值字符串等。
        - 当运算结果数学上无定义（如负数开小数次方）、或输入无法转换为数值时返回 None。
        - 本函数不抛出异常，也不打印错误信息。

    Args:
        基数 (SupportsFloat): 幂运算的底数。
        指数 (SupportsFloat): 幂运算的指数。

    Returns:
        float | None:
            - 成功：返回幂运算结果（float 类型）。
            - 失败：返回 None（输入非法或运算不符合数学定义）。

    Notes:
        - 与 math.pow 的差异：
            * a ** b 支持复数运算，而 math.pow 不支持。
            * a ** b 可能返回 int，而 math.pow 始终返回 float。
        - 为保证类型一致性，本函数最终返回 float。
        - 若需要严格整数幂或模幂运算，可另行编写专用函数。
    """
    try:
        x = float(基数)
        y = float(指数)
        return float(x ** y)
    except Exception:
        return None
