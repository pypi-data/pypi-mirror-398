from typing import SupportsFloat, Optional


def 限制范围(
    数值: SupportsFloat,
    最小值: SupportsFloat,
    最大值: SupportsFloat
) -> Optional[float]:
    """
    将数值限制在指定的最小值与最大值区间内（Clamp）。

    功能说明：
        - 若数值小于最小值，则返回最小值。
        - 若数值大于最大值，则返回最大值。
        - 若数值在区间内，则返回其本身。
        - 所有输入都将尝试转换为 float，失败时返回 None。
        - 若最小值大于最大值，返回 None（参数无效）。

    Args:
        数值 (SupportsFloat): 需要被限制的数值。
        最小值 (SupportsFloat): 区间下界。
        最大值 (SupportsFloat): 区间上界。

    Returns:
        float | None:
            - 成功：返回限制后的数值。
            - 失败：返回 None。

    Notes:
        - Clamp 是图形学、数学、游戏开发、归一化处理中常见功能。
        - 典型用法包括限制百分比、限制属性范围、预防计算越界等。
    """
    try:
        x = float(数值)
        mn = float(最小值)
        mx = float(最大值)

        if mn > mx:
            return None

        if x < mn:
            return mn
        if x > mx:
            return mx

        return x

    except Exception:
        return None
