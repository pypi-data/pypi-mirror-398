from typing import SupportsFloat, Optional
import math


def 坐标_点是否在线段上(
    ax: SupportsFloat,
    ay: SupportsFloat,
    bx: SupportsFloat,
    by: SupportsFloat,
    px: SupportsFloat,
    py: SupportsFloat,
    az: SupportsFloat | None = None,
    bz: SupportsFloat | None = None,
    pz: SupportsFloat | None = None,
    *,
    容差: SupportsFloat = 1e-9,
) -> Optional[bool]:
    """
    判断点是否位于线段上（支持二维与三维坐标）。

    功能说明：
        - 判断点 P 是否落在线段 AB 上（包含端点 A、B）。
        - 支持二维和三维：
            * 若 az、bz、pz 均不为 None，则按三维计算；
            * 否则按二维计算。
        - 判断逻辑分三步：
            1) 三点是否共线（或共线到一定容差范围内）
            2) P 在不在 A 与 B 之间（不在延长线上）
            3) 处理退化情况：若 A 和 B 重合，则线段退化为点，
               此时只要 P 与该点足够接近即可视为在线段上。
        - 任意参数无法转换为数值时，返回 None。
        - 本函数不抛出异常，适合作为底层坐标/几何工具函数。

    Args:
        ax (SupportsFloat): 线段起点 A 的 X 坐标。
        ay (SupportsFloat): 线段起点 A 的 Y 坐标。
        bx (SupportsFloat): 线段终点 B 的 X 坐标。
        by (SupportsFloat): 线段终点 B 的 Y 坐标。
        px (SupportsFloat): 测试点 P 的 X 坐标。
        py (SupportsFloat): 测试点 P 的 Y 坐标。
        az (SupportsFloat | None): 起点 A 的 Z 坐标，可选。
        bz (SupportsFloat | None): 终点 B 的 Z 坐标，可选。
        pz (SupportsFloat | None): 测试点 P 的 Z 坐标，可选。
        容差 (SupportsFloat, optional): 浮点误差容忍范围，默认 1e-9。

    Returns:
        bool | None:
            - True：点在线段上（包含端点）。
            - False：点不在线段上。
            - None：输入无法转换为数值等异常情况。

    Notes:
        - 二维情况：
            1) 使用“有向面积”为 0 判定共线：
                   S2 = (bx - ax) * (py - ay) - (px - ax) * (by - ay)
               若 |S2| <= 容差，则认为共线。
            2) 使用点积判断 P 是否在 A 和 B 之间：
                   AP·AB 在 [0, |AB|^2] 范围内则在线段上。

        - 三维情况：
            1) 使用向量叉积 AB × AP 的长度接近 0 判定共线。
            2) 同样用点积判断是否处于线段内。

        - 若 A 与 B 重合（线段退化为点），则只要 P 与该点距离
          小于等于 容差，即视为“在线段上”。
    """
    try:
        ax_f = float(ax)
        ay_f = float(ay)
        bx_f = float(bx)
        by_f = float(by)
        px_f = float(px)
        py_f = float(py)
        eps = float(容差)

        # 处理三维情况
        if az is not None and bz is not None and pz is not None:
            az_f = float(az)
            bz_f = float(bz)
            pz_f = float(pz)

            # 向量 AB = B - A, AP = P - A
            abx = bx_f - ax_f
            aby = by_f - ay_f
            abz = bz_f - az_f

            apx = px_f - ax_f
            apy = py_f - ay_f
            apz = pz_f - az_f

            # 线段退化：A 与 B 重合
            if abx == 0 and aby == 0 and abz == 0:
                # 只要 P 与 A 足够接近，就视为在线段上
                dist2 = apx * apx + apy * apy + apz * apz
                return dist2 <= eps * eps

            # 1) 共线判断：|AB × AP| 是否接近 0
            cx = aby * apz - abz * apy
            cy = abz * apx - abx * apz
            cz = abx * apy - aby * apx
            cross_len = math.sqrt(cx * cx + cy * cy + cz * cz)
            if cross_len > eps:
                return False

            # 2) 判断 P 是否在 A 与 B 之间：检查 AP 在 AB 上的投影范围
            dot_ap_ab = apx * abx + apy * aby + apz * abz
            ab_len2 = abx * abx + aby * aby + abz * abz

            if dot_ap_ab < -eps or dot_ap_ab > ab_len2 + eps:
                return False

            return True

        # 二维情况
        abx = bx_f - ax_f
        aby = by_f - ay_f
        apx = px_f - ax_f
        apy = py_f - ay_f

        # 线段退化：A 与 B 重合
        if abx == 0 and aby == 0:
            dist2 = apx * apx + apy * apy
            return dist2 <= eps * eps

        # 1) 共线判断（有向面积为 0）
        s2 = abx * apy - apx * aby
        if abs(s2) > eps:
            return False

        # 2) 判断投影是否在 [0, |AB|^2] 范围内
        dot_ap_ab = apx * abx + apy * aby
        ab_len2 = abx * abx + aby * aby

        if dot_ap_ab < -eps or dot_ap_ab > ab_len2 + eps:
            return False

        return True

    except Exception:
        return None
