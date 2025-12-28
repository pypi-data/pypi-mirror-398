from typing import SupportsFloat, Optional, Tuple


def 坐标_叉积(
    x1: SupportsFloat,
    y1: SupportsFloat,
    z1: SupportsFloat,
    x2: SupportsFloat,
    y2: SupportsFloat,
    z2: SupportsFloat,
) -> Optional[Tuple[float, float, float]]:
    """
    计算两个三维向量的叉积（Cross Product），返回法向量。

    功能说明：
        - 叉积是三维向量中特别重要的运算，其结果为一个
          *垂直于两个输入向量* 的新向量（法向量）。
        - 叉积的方向由右手定则决定：
              A × B 的方向 = 右手四指从 A 卷向 B，大拇指指向的方向
        - 叉积长度公式：
              |A×B| = |A| * |B| * sin(θ)
          也代表两个向量围成的平行四边形面积。
        - 所有参数会尝试转换为 float，失败返回 None。
        - 本函数不抛异常，是底层坐标工具函数的安全实现。

    Args:
        x1, y1, z1 (SupportsFloat): 向量 A 的三个分量。
        x2, y2, z2 (SupportsFloat): 向量 B 的三个分量。

    Returns:
        tuple[float, float, float] | None:
            成功：返回法向量 (cx, cy, cz)
            失败：返回 None

    Notes:
        数学公式：
            A × B = (
                y1*z2 - z1*y2,
                z1*x2 - x1*z2,
                x1*y2 - y1*x2
            )

        特别说明：
            - 若 A 与 B 平行（包括同向、反向），叉积为 (0,0,0)
            - 若你只需要判断左右关系，可观察返回向量的方向符号
    """
    try:
        x1_f = float(x1)
        y1_f = float(y1)
        z1_f = float(z1)

        x2_f = float(x2)
        y2_f = float(y2)
        z2_f = float(z2)

        cx = y1_f * z2_f - z1_f * y2_f
        cy = z1_f * x2_f - x1_f * z2_f
        cz = x1_f * y2_f - y1_f * x2_f

        return (cx, cy, cz)

    except Exception:
        return None
