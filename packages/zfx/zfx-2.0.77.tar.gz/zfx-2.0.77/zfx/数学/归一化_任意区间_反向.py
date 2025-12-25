from typing import SupportsFloat, Optional


def 归一化_任意区间_反向(
    数值: SupportsFloat,
    原最小值: SupportsFloat,
    原最大值: SupportsFloat,
    目标最小值: SupportsFloat,
    目标最大值: SupportsFloat
) -> Optional[float]:
    """
    将目标区间的数值反向映射回原始区间。

    功能说明：
        - 输入区间为 [目标最小值, 目标最大值]。
        - 输出区间为 [原最小值, 原最大值]。
        - 若目标区间大小为 0（目标最小值 == 目标最大值），返回 None。
        - 所有输入会尝试转换为 float，失败则返回 None。

    反向映射公式：
        t = (数值 - 目标最小值) / (目标最大值 - 目标最小值)
        原值 = 原最小值 + t * (原最大值 - 原最小值)

    Args:
        数值 (SupportsFloat): 处于目标区间的新值。
        原最小值 (SupportsFloat): 原区间最小值。
        原最大值 (SupportsFloat): 原区间最大值。
        目标最小值 (SupportsFloat): 目标区间最小值。
        目标最大值 (SupportsFloat): 目标区间最大值。

    Returns:
        float | None:
            - 成功：返回反向映射后的原始数值。
            - 失败：返回 None。

    Notes:
        - 即“归一化_任意区间”的逆操作。
        - 适合需要恢复真实数值的场景，如评分系统、数据压缩等。
    """
    try:
        y = float(数值)
        a = float(原最小值)
        b = float(原最大值)
        c = float(目标最小值)
        d = float(目标最大值)

        if d == c:
            return None

        t = (y - c) / (d - c)
        return a + t * (b - a)

    except Exception:
        return None
