from typing import SupportsFloat, Optional


def 线性插值(
    起点: SupportsFloat,
    终点: SupportsFloat,
    比例值: SupportsFloat
) -> Optional[float]:
    """
    根据比例值在线性区间内计算插值（Lerp）。

    功能说明：
        - Lerp 用于根据比例值在线段 [起点, 终点] 内取得对应的中间值。
        - 比例值通常在 0 到 1 范围内：
            t = 0   → 返回起点
            t = 1   → 返回终点
            t = 0.5 → 返回正中间
        - 若比例值超出 0～1，函数仍按数学公式正常外推。
        - 所有输入将尝试转换为 float，失败时返回 None。

    插值公式：
        插值结果 = 起点 + (终点 - 起点) * 比例值

    Args:
        起点 (SupportsFloat): 插值起点。
        终点 (SupportsFloat): 插值终点。
        比例值 (SupportsFloat): 插值比例值 t，通常为 0～1 之间的浮点数。

    Returns:
        float | None:
            - 成功：返回插值结果。
            - 失败：返回 None。

    Notes:
        - 若希望限制比例值范围，可搭配“限制范围（Clamp）”函数使用。
        - 本函数是许多动画、过渡、平滑运动等计算的核心基础。
    """
    try:
        a = float(起点)
        b = float(终点)
        t = float(比例值)

        return a + (b - a) * t

    except Exception:
        return None
