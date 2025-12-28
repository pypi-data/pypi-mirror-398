from typing import SupportsFloat, Optional


def 归一化_0到1_反向(
    比例值: SupportsFloat,
    最小值: SupportsFloat,
    最大值: SupportsFloat
) -> Optional[float]:
    """
    将 [0, 1] 区间的比例值反向映射回原始数值范围。

    功能说明：
        - 输入为 0 到 1 区间内的比例值（归一化结果）。
        - 输出为对应的真实数值，范围为 [最小值, 最大值]。
        - 若最大值与最小值相同，无法进行映射，将返回 None。
        - 输入类型无法转换为 float 时返回 None。

    映射公式：
        原始值 = 最小值 + 比例值 * (最大值 - 最小值)

    Args:
        比例值 (SupportsFloat): 归一化比例值，通常为 0 到 1 之间的浮点数。
        最小值 (SupportsFloat): 原区间的最小值。
        最大值 (SupportsFloat): 原区间的最大值。

    Returns:
        float | None:
            - 成功：返回反归一化后的原始数值。
            - 失败：返回 None。

    Notes:
        - 若比例值超出 0～1 区间，计算仍按公式执行（会得到区间外的结果）。
        - 若需要限制比例值，可结合“限制范围（Clamp）”功能使用。
    """
    try:
        t = float(比例值)
        mn = float(最小值)
        mx = float(最大值)

        if mx == mn:
            return None

        return mn + t * (mx - mn)

    except Exception:
        return None