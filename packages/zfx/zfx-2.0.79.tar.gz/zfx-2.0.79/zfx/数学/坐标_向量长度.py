from typing import SupportsFloat, Optional
import math


def 坐标_向量长度(
    dx: SupportsFloat,
    dy: SupportsFloat,
    dz: SupportsFloat | None = None,
) -> Optional[float]:
    """
    计算向量的长度（支持二维与三维向量）。

    功能说明：
        - 输入为向量分量 (dx, dy) 或 (dx, dy, dz)。
        - 若 dz 缺失，则计算二维向量长度。
        - 所有输入会尝试转换为 float；若任意值无法转换，则返回 None。
        - 本函数不抛出异常，作为底层数学/坐标工具函数安全可靠。

    Args:
        dx (SupportsFloat): 向量在 X 轴方向的分量。
        dy (SupportsFloat): 向量在 Y 轴方向的分量。
        dz (SupportsFloat | None): 向量在 Z 轴方向的分量，可选。

    Returns:
        float | None: 成功返回向量长度（float），失败返回 None。

    Notes:
        - 二维长度公式：sqrt(dx^2 + dy^2)
        - 三维长度公式：sqrt(dx^2 + dy^2 + dz^2)
        - 向量长度总是返回非负数。
    """
    try:
        dx_f = float(dx)
        dy_f = float(dy)

        if dz is not None:
            dz_f = float(dz)
            return math.sqrt(dx_f**2 + dy_f**2 + dz_f**2)

        return math.sqrt(dx_f**2 + dy_f**2)

    except Exception:
        return None
