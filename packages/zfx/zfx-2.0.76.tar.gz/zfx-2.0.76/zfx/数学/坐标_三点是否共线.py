from typing import SupportsFloat, Optional
import math


def 坐标_三点是否共线(
    x1: SupportsFloat,
    y1: SupportsFloat,
    x2: SupportsFloat,
    y2: SupportsFloat,
    x3: SupportsFloat,
    y3: SupportsFloat,
    z1: SupportsFloat | None = None,
    z2: SupportsFloat | None = None,
    z3: SupportsFloat | None = None,
    *,
    容差: SupportsFloat = 1e-9,
) -> Optional[bool]:
    """
    判断三点是否共线（支持二维与三维坐标）。

    功能说明：
        - 用于判断三点是否在同一条直线上：
            * 在二维中：三点是否在同一条平面直线上。
            * 在三维中：三点是否在同一条空间直线上。
        - 若启用三维判断（z1, z2, z3 均不为 None），使用向量叉积长度判断；
          否则按二维坐标判断。
        - 浮点运算中，完全等于 0 几乎不可能，因此提供“容差”概念：
            只要“偏离程度”小于等于容差，就视为共线。
        - 任意一个参数无法转换为数值时，返回 None。
        - 本函数不抛出异常，适合作为底层数学/坐标工具函数。

    Args:
        x1 (SupportsFloat): 第一个点的 X 坐标。
        y1 (SupportsFloat): 第一个点的 Y 坐标。
        x2 (SupportsFloat): 第二个点的 X 坐标。
        y2 (SupportsFloat): 第二个点的 Y 坐标。
        x3 (SupportsFloat): 第三个点的 X 坐标。
        y3 (SupportsFloat): 第三个点的 Y 坐标。
        z1 (SupportsFloat | None): 第一个点的 Z 坐标，可选。
        z2 (SupportsFloat | None): 第二个点的 Z 坐标，可选。
        z3 (SupportsFloat | None): 第三个点的 Z 坐标，可选。
        容差 (SupportsFloat, optional): 判断误差容忍范围，默认 1e-9。

    Returns:
        bool | None:
            - True：三点视为共线。
            - False：三点不共线。
            - None：输入无法转换为数值等异常情况。

    Notes:
        - 二维判断实现：
              使用三角形面积的两倍：
                  S2 = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
              若 |S2| <= 容差，则认为共线。
        - 三维判断实现：
              计算 AB = B - A, AC = C - A
              若叉积 AB × AC 的长度接近 0，则认为共线。
        - 若三点中有重复点：
              例如 A = B 或 B = C 等，仍然视为共线（退化为一条线上的两个点）。
    """
    try:
        x1_f = float(x1)
        y1_f = float(y1)
        x2_f = float(x2)
        y2_f = float(y2)
        x3_f = float(x3)
        y3_f = float(y3)
        eps = float(容差)

        # 三维判断
        if z1 is not None and z2 is not None and z3 is not None:
            z1_f = float(z1)
            z2_f = float(z2)
            z3_f = float(z3)

            # 向量 AB = B - A, AC = C - A
            abx = x2_f - x1_f
            aby = y2_f - y1_f
            abz = z2_f - z1_f

            acx = x3_f - x1_f
            acy = y3_f - y1_f
            acz = z3_f - z1_f

            # 叉积 AB × AC
            cx = aby * acz - abz * acy
            cy = abz * acx - abx * acz
            cz = abx * acy - aby * acx

            cross_len = math.sqrt(cx * cx + cy * cy + cz * cz)
            return cross_len <= eps

        # 二维判断：使用“面积为 0”判定共线
        s2 = (x2_f - x1_f) * (y3_f - y1_f) - (x3_f - x1_f) * (y2_f - y1_f)
        return abs(s2) <= eps

    except Exception:
        return None