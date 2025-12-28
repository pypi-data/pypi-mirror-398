from typing import SupportsFloat, Optional


def 归一化_任意区间(
    数值: SupportsFloat,
    原最小值: SupportsFloat,
    原最大值: SupportsFloat,
    目标最小值: SupportsFloat,
    目标最大值: SupportsFloat
) -> Optional[float]:
    """
    将数值从原始区间映射到新区间。

    功能说明：
        - 输入区间为 [原最小值, 原最大值]。
        - 输出区间为 [目标最小值, 目标最大值]。
        - 若原区间大小为 0（原最小值 == 原最大值），返回 None。
        - 所有输入会尝试转换为 float，失败则返回 None。

    映射公式：
        t = (数值 - 原最小值) / (原最大值 - 原最小值)
        映射值 = 目标最小值 + t * (目标最大值 - 目标最小值)

    Args:
        数值 (SupportsFloat): 需要映射的原始数值。
        原最小值 (SupportsFloat): 原区间最小值。
        原最大值 (SupportsFloat): 原区间最大值。
        目标最小值 (SupportsFloat): 目标区间最小值。
        目标最大值 (SupportsFloat): 目标区间最大值。

    Returns:
        float | None:
            - 成功：返回映射后的新数值。
            - 失败：返回 None。

    Notes:
        - 若数值超出原区间，会按数学公式正常外推。
        - 本函数本质是“区间映射”，归一化是它的特例。
    """
    try:
        x = float(数值)
        a = float(原最小值)
        b = float(原最大值)
        c = float(目标最小值)
        d = float(目标最大值)

        if b == a:
            return None

        t = (x - a) / (b - a)
        return c + t * (d - c)

    except Exception:
        return None