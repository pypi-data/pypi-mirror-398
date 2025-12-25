import math
from typing import SupportsFloat, Optional

def 反三角_余弦(数值: SupportsFloat) -> Optional[float]:
    """
    计算反余弦值（arccos），返回弧度制结果。

    功能说明：
        - 计算 arccos(数值)，返回弧度制角度。
        - 输入必须在 [-1, 1] 范围内，否则数学上无定义，将返回 None。
        - 支持所有可转换为 float 的类型。

    Args:
        数值 (SupportsFloat): 需要计算反余弦的数值。

    Returns:
        float | None:
            - 成功：返回反余弦值（弧度）。
            - 失败：返回 None（输入格式非法或超出 [-1, 1]）。

    Notes:
        - 等价于：math.acos(数值)。
        - 返回值范围通常为 [0, π]。
    """
    try:
        x = float(数值)
        return math.acos(x)
    except Exception:
        return None