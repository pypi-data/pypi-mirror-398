import math
from typing import SupportsFloat, Optional

def 反三角_正切(数值: SupportsFloat) -> Optional[float]:
    """
    计算反正切值（arctan），返回弧度制结果。

    功能说明：
        - 计算 arctan(数值)，返回弧度制角度。
        - 支持所有可转换为 float 的类型，输入可为任意实数。
        - 若输入无法转换为 float，则返回 None。

    Args:
        数值 (SupportsFloat): 需要计算反正切的数值。

    Returns:
        float | None:
            - 成功：返回反正切值（弧度）。
            - 失败：返回 None（输入格式非法）。

    Notes:
        - 等价于：math.atan(数值)。
        - 返回值范围通常为 (-π/2, π/2)。
    """
    try:
        x = float(数值)
        return math.atan(x)
    except Exception:
        return None