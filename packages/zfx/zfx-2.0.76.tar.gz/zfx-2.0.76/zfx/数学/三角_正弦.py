import math
from typing import SupportsFloat, Optional

def 三角_正弦(角度: SupportsFloat) -> Optional[float]:
    """
    计算角度制数值的正弦值（sin）。

    功能说明：
        - 输入为角度制（degrees），内部自动转换为弧度制（radians）。
        - 支持所有可转换为 float 的类型。
        - 若输入无法转换为浮点数，则返回 None。

    Args:
        角度 (SupportsFloat): 角度制的角度值。

    Returns:
        float | None:
            - 成功：返回正弦值（范围 [-1, 1]）。
            - 失败：返回 None。

    Notes:
        - 等价于：math.sin(math.radians(角度))。
        - 与三角_余弦 一样，统一使用角度制输入的封装形式。
    """
    try:
        弧度 = math.radians(float(角度))
        return math.sin(弧度)
    except Exception:
        return None