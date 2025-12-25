from typing import SupportsFloat, Optional
import math


def 坐标_两向量夹角(
    x1: SupportsFloat,
    y1: SupportsFloat,
    x2: SupportsFloat,
    y2: SupportsFloat,
    z1: SupportsFloat | None = None,
    z2: SupportsFloat | None = None,
) -> Optional[float]:
    """
    计算两个向量的夹角（单位：度），支持二维与三维。

    功能说明：
        - 返回两个向量之间的几何夹角，范围固定为 0°~180°。
        - 当任一向量长度为 0（方向不存在）时，返回 None。
        - 所有输入尝试转换为 float，失败则返回 None。
        - 本函数安全，不抛异常，适合作为底层数学/坐标工具函数。

    Args:
        x1, y1 (SupportsFloat): 向量 A 的二维分量。
        x2, y2 (SupportsFloat): 向量 B 的二维分量。
        z1, z2 (SupportsFloat | None): 向量 A 与 B 的三维分量，可选。

    Returns:
        float | None:
            成功：返回夹角（度数，0~180）。
            失败：返回 None。

    Notes:
        数学公式：
            cosθ = dot(A, B) / (|A| * |B|)
            θ = arccos(cosθ)

        为避免浮点误差导致 acos 报错，内部会将 cosθ 限制在 [-1, 1] 范围内。
    """
    try:
        # 转换数值
        x1_f, y1_f = float(x1), float(y1)
        x2_f, y2_f = float(x2), float(y2)

        # 处理三维情况
        if z1 is not None and z2 is not None:
            z1_f, z2_f = float(z1), float(z2)

            # 向量长度
            len_a = math.sqrt(x1_f**2 + y1_f**2 + z1_f**2)
            len_b = math.sqrt(x2_f**2 + y2_f**2 + z2_f**2)
            if len_a == 0 or len_b == 0:
                return None

            # 点积
            dot = x1_f * x2_f + y1_f * y2_f + z1_f * z2_f

        else:
            # 2D
            len_a = math.sqrt(x1_f**2 + y1_f**2)
            len_b = math.sqrt(x2_f**2 + y2_f**2)
            if len_a == 0 or len_b == 0:
                return None

            dot = x1_f * x2_f + y1_f * y2_f

        # cosθ
        cos_theta = dot / (len_a * len_b)

        # 防止浮点误差导致 cosθ 略超界（如 1.0000001）
        cos_theta = max(min(cos_theta, 1.0), -1.0)

        # 求夹角（弧度→度）
        angle_rad = math.acos(cos_theta)
        return math.degrees(angle_rad)

    except Exception:
        return None
