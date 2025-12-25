import math
from typing import SupportsFloat, Optional


def 向上取整(数值: SupportsFloat) -> Optional[int]:
    """
    返回不小于指定数值的最小整数（向上取整）。

    功能说明：
        - 使用标准库 math.ceil 执行向上取整。
        - 支持所有可转换为 float 的输入（如 int、float、可数值字符串等）。
        - 若输入无法转换为数值，将返回 None，而不会抛出异常或打印错误信息。
        - 返回值为整数类型，适用于数学运算、分页逻辑、数据处理等场景。

    Args:
        数值 (SupportsFloat): 任意可转换为浮点数的数值类型。

    Returns:
        int | None:
            - 成功：返回向上取整后的整数值。
            - 失败：返回 None（如输入格式非法）。

    Notes:
        - math.ceil 始终返回 int 类型，即使输入为浮点数。
        - 本函数仅对数值转换与错误处理做封装，不改变 ceil 的行为。
    """
    try:
        return math.ceil(float(数值))
    except Exception:
        return None