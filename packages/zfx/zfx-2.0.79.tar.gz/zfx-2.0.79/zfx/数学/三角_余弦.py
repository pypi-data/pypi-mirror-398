import math
from typing import SupportsFloat, Optional


def 三角_余弦(角度: SupportsFloat) -> Optional[float]:
    """
    计算角度制数值的余弦值（cos）。

    功能说明：
        - 输入为角度制（degrees），内部自动转换为弧度制（radians）。
        - 支持所有可转换为 float 的类型，例如：int、float、可数值字符串等。
        - 若输入无法转换为浮点数，则返回 None，不抛出异常、不打印错误。

    Args:
        角度 (SupportsFloat): 角度制的角度值。

    Returns:
        float | None:
            - 成功：返回余弦值（范围 [-1, 1]）。
            - 失败：返回 None（输入格式非法等）。

    Notes:
        - 等价于：math.cos(math.radians(角度))。
        - 若需要弧度制输入，请直接使用 math.cos()。
    """
    try:
        弧度 = math.radians(float(角度))
        return math.cos(弧度)
    except Exception:
        return None