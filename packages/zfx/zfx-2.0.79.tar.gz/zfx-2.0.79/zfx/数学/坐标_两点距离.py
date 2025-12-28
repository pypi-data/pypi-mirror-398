from typing import SupportsFloat, Optional
import math


def 坐标_两点距离(
        x1: SupportsFloat,
        y1: SupportsFloat,
        x2: SupportsFloat,
        y2: SupportsFloat,
        z1: SupportsFloat | None = None,
        z2: SupportsFloat | None = None,
) -> Optional[float]:
    """
    计算两点之间的距离（支持 2D / 3D）。

    功能说明：
        - 若仅提供 x 与 y，使用二维距离公式。
        - 若同时提供 z1 与 z2，自动切换为三维距离计算。
        - 所有输入会尝试转换为浮点数；若任意值无法转换，则返回 None。
        - 本函数不抛出异常，是底层数学工具函数的安全写法。

    Args:
        x1, y1, x2, y2 (SupportsFloat): 两点的平面坐标，可为 int/float/数值字符串。
        z1, z2 (SupportsFloat | None): 可选的高度坐标，若都提供则使用三维距离。

    Returns:
        float | None: 成功返回距离值（float），失败返回 None。

    Notes:
        - 2D 公式：sqrt((x2 - x1)^2 + (y2 - y1)^2)
        - 3D 公式：sqrt((x2 - x1)^2 + (y2 - y1)^2 + (z2 - z1)^2)
    """
    try:
        x1 = float(x1)
        y1 = float(y1)
        x2 = float(x2)
        y2 = float(y2)

        if z1 is not None and z2 is not None:
            z1 = float(z1)
            z2 = float(z2)
            return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    except Exception:
        return None
