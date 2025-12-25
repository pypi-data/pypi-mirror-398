from typing import SupportsFloat, Optional
import math


def 坐标_方向角(
    x1: SupportsFloat,
    y1: SupportsFloat,
    x2: SupportsFloat,
    y2: SupportsFloat,
) -> Optional[float]:
    """
    计算从起点指向终点的方向角（0~360 度，以正北为 0 度）。

    功能说明：
        - 基于平面坐标 (x, y) 计算从起点 -> 终点的朝向角度。
        - 假设坐标系：
            * X 轴向右为正
            * Y 轴向上为正，且 Y 正方向为“正北”
        - 返回角度范围：0 <= 角度 < 360
            * 0   度：正北（Y 递增方向）
            * 90  度：正东（X 递增方向）
            * 180 度：正南
            * 270 度：正西
        - 若起点与终点重合（两点坐标完全相同），方向角没有意义，返回 None。
        - 所有输入会尝试转换为浮点数；若任意值无法转换，则返回 None。
        - 本函数不抛出异常，适合作为底层数学/坐标工具函数。

    Args:
        x1 (SupportsFloat): 起点的 X 坐标，可为 int/float/数值字符串等。
        y1 (SupportsFloat): 起点的 Y 坐标。
        x2 (SupportsFloat): 终点的 X 坐标。
        y2 (SupportsFloat): 终点的 Y 坐标。

    Returns:
        float | None: 成功返回方向角（单位：度，范围 0~360），失败返回 None。

    Notes:
        - 内部使用 `math.atan2(dy, dx)` 计算相对 +X 轴逆时针角度，
          再转换为以“正北”为 0 度的表示方式：
              原始角度 = atan2(dy, dx)（弧度）
              转为角度 = degrees(原始角度)
              北向角度 = (90 - 转为角度) % 360
    """
    try:
        x1_f = float(x1)
        y1_f = float(y1)
        x2_f = float(x2)
        y2_f = float(y2)

        dx = x2_f - x1_f
        dy = y2_f - y1_f

        # 起点与终点重合时，方向没有定义
        if dx == 0 and dy == 0:
            return None

        # atan2 返回：相对 X 正方向，逆时针为正的角度（弧度）
        rad = math.atan2(dy, dx)
        deg = math.degrees(rad)

        # 转换为：以正北为 0 度，顺时针增加的角度
        angle_north = (90.0 - deg) % 360.0
        return angle_north

    except Exception:
        return None