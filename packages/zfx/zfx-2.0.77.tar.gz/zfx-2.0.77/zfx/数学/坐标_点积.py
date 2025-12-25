from typing import SupportsFloat, Optional
import math


def 坐标_点积(
        x1: SupportsFloat,
        y1: SupportsFloat,
        x2: SupportsFloat,
        y2: SupportsFloat,
        z1: SupportsFloat | None = None,
        z2: SupportsFloat | None = None,
) -> Optional[float]:
    """
    计算两个向量的点积（Dot Product），支持二维与三维。

    功能说明：
        - 点积是向量之间最重要的运算之一，用来衡量两个方向的关系。
        - 点积公式：
            二维：x1*x2 + y1*y2
            三维：x1*x2 + y1*y2 + z1*z2
        - 点积结果含义：
            > 0：方向大致相同
            = 0：完全垂直（正交）
            < 0：方向相反
        - 输入必须是向量分量而非两点坐标。
        - 任意参数无法转换为数字或其它异常 → 返回 None。
        - 本函数不抛异常，适合底层数学/坐标工具函数。

    Args:
        x1 (SupportsFloat): 向量 A 的 X 分量。
        y1 (SupportsFloat): 向量 A 的 Y 分量。
        x2 (SupportsFloat): 向量 B 的 X 分量。
        y2 (SupportsFloat): 向量 B 的 Y 分量。
        z1 (SupportsFloat | None): 向量 A 的 Z 分量，可选。
        z2 (SupportsFloat | None): 向量 B 的 Z 分量，可选。

    Returns:
        float | None: 成功返回点积值；失败返回 None。

    Notes:
        - 若想求夹角，可结合：
              cosθ = dot(A, B) / (|A| * |B|)
        - 点积对方向判断非常有用：
            dot > 0 → 同方向
            dot = 0 → 垂直
            dot < 0 → 反方向
    """
    try:
        x1_f = float(x1)
        y1_f = float(y1)
        x2_f = float(x2)
        y2_f = float(y2)

        # 3D
        if z1 is not None and z2 is not None:
            z1_f = float(z1)
            z2_f = float(z2)
            return x1_f * x2_f + y1_f * y2_f + z1_f * z2_f

        # 2D
        return x1_f * x2_f + y1_f * y2_f

    except Exception:
        return None