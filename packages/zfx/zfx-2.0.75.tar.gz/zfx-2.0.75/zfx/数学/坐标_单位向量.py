from typing import SupportsFloat, Optional, Tuple
import math


def 坐标_单位向量(
    dx: SupportsFloat,
    dy: SupportsFloat,
    dz: SupportsFloat | None = None,
) -> Optional[Tuple[float, ...]]:
    """
    计算向量的单位向量（归一化向量），支持二维与三维。

    功能说明：
        - 将向量 (dx, dy) 或 (dx, dy, dz) 归一化，使其长度变为 1。
        - 若向量长度为 0（如 dx=dy=dz=0），则方向不存在，返回 None。
        - 所有输入会尝试转换成 float；若任意值无法转换，则返回 None。
        - 本函数不抛异常，是底层数学/坐标工具函数的安全实现。

    Args:
        dx (SupportsFloat): 向量在 X 轴方向的分量。
        dy (SupportsFloat): 向量在 Y 轴方向的分量。
        dz (SupportsFloat | None): 向量在 Z 轴方向的分量，可选。

    Returns:
        tuple[float, ...] | None:
            成功：返回单位向量 (ux, uy) 或 (ux, uy, uz)
            失败：返回 None

    Notes:
        - 单位向量定义：v / |v|
        - |v| 为向量长度，若为 0 则单位向量不存在。
    """
    try:
        dx_f = float(dx)
        dy_f = float(dy)

        if dz is not None:
            dz_f = float(dz)
            length = math.sqrt(dx_f**2 + dy_f**2 + dz_f**2)
            if length == 0:
                return None
            return (dx_f / length, dy_f / length, dz_f / length)

        # 2D
        length = math.sqrt(dx_f**2 + dy_f**2)
        if length == 0:
            return None
        return (dx_f / length, dy_f / length)

    except Exception:
        return None
