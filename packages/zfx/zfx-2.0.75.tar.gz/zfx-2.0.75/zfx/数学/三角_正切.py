import math
from typing import SupportsFloat, Optional

def 三角_正切(角度: SupportsFloat) -> Optional[float]:
    """
    计算角度制数值的正切值（tan）。

    功能说明：
        - 输入为角度制（degrees），内部自动转换为弧度制（radians）。
        - 支持所有可转换为 float 的类型。
        - 若输入无法转换为浮点数，则返回 None。
        - 当角度接近奇数个 90°（例如 90°, 270°）时，正切值会非常大，
          这是数学上 tan(x) 在这些点附近趋于无穷的数值体现。

    Args:
        角度 (SupportsFloat): 角度制的角度值。

    Returns:
        float | None:
            - 成功：返回正切值（float）。
            - 失败：返回 None。

    Notes:
        - 等价于：math.tan(math.radians(角度))。
        - 对于 90° + k·180°，tan 理论上无定义，在浮点环境中会得到非常大的数值。
    """
    try:
        弧度 = math.radians(float(角度))
        return math.tan(弧度)
    except Exception:
        return None