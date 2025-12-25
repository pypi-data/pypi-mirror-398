import math
from typing import SupportsFloat, Optional


def 近似相等(
    数值1: SupportsFloat,
    数值2: SupportsFloat,
    *,
    相对误差: float = 1e-9,
    绝对误差: float = 0.0
) -> Optional[bool]:
    """
    判断两个数值在允许误差范围内是否近似相等。

    功能说明：
        - 对浮点数进行安全比较，不建议直接使用 ==。
        - 支持设置相对误差与绝对误差。
        - 若输入无法转换为浮点数，则返回 None。

    Args:
        数值1 (SupportsFloat): 第一个数值。
        数值2 (SupportsFloat): 第二个数值。
        相对误差 (float): 允许的相对误差，默认 1e-9。
        绝对误差 (float): 允许的绝对误差，默认 0.0。

    Returns:
        bool | None:
            - True：两数值近似相等。
            - False：不相等。
            - None：输入无效。

    Notes:
        - 内部使用 math.isclose 实现。
        - 适用于价格比较、角度比较、坐标浮点误差处理等场景。
    """
    try:
        x = float(数值1)
        y = float(数值2)
        return math.isclose(x, y, rel_tol=相对误差, abs_tol=绝对误差)
    except Exception:
        return None
