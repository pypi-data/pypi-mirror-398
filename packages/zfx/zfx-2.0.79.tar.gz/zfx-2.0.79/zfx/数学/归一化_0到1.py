from typing import SupportsFloat, Optional


def 归一化_0到1(
    数值: SupportsFloat,
    最小值: SupportsFloat,
    最大值: SupportsFloat
) -> Optional[float]:
    """
    将数值归一化到 0 到 1 区间。

    功能说明：
        - 根据给定的最小值与最大值，将数值映射到 [0, 1] 范围。
        - 常用于数据缩放、评分、机器学习预处理等场景。
        - 若最大值等于最小值，或输入无法转换为浮点数，则返回 None。

    归一化公式：
        (数值 - 最小值) / (最大值 - 最小值)

    Args:
        数值 (SupportsFloat): 需要归一化的数值。
        最小值 (SupportsFloat): 原始数据的最小值。
        最大值 (SupportsFloat): 原始数据的最大值。

    Returns:
        float | None:
            - 成功：返回归一化结果（范围 0 到 1 之间）。
            - 失败：返回 None。

    Notes:
        - 当最大值等于最小值时无法进行归一化（除以 0），将返回 None。
        - 输入值位于范围外时，结果可能 <0 或 >1，此属于正常数学行为。
    """
    try:
        x = float(数值)
        mn = float(最小值)
        mx = float(最大值)

        if mx == mn:
            return None

        return (x - mn) / (mx - mn)

    except Exception:
        return None