import math
from typing import SupportsFloat, Optional


def 向下取整(数值: SupportsFloat) -> Optional[int]:
    """
    返回不大于指定数值的最大整数（向下取整）。

    功能说明：
        - 使用 math.floor 执行向下取整。
        - 支持所有能够转换为 float 的输入类型，例如 int、float、可数值字符串等。
        - 若输入无法转换为数值，返回 None，不抛异常、不打印错误信息。
        - 返回结果始终为 int 类型，适用于数学运算、分页计算、边界处理等场景。

    Args:
        数值 (SupportsFloat): 任意可被转换为浮点数的值。

    Returns:
        int | None:
            - 成功：返回向下取整后的整数。
            - 失败：返回 None（输入非法或无法转换为 float）。

    Notes:
        - math.floor 的行为：对正数类似于向左取整，对负数则向更小的整数方向取整。
        - 本函数仅封装数值转换与异常处理，不改变 floor 的数学语义。
    """
    try:
        return math.floor(float(数值))
    except Exception:
        return None
