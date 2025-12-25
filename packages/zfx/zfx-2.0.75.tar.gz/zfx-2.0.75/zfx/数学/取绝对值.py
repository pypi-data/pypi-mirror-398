from typing import SupportsFloat, Optional


def 取绝对值(数值: SupportsFloat) -> Optional[float]:
    """
    返回指定数值的绝对值。

    功能说明：
        - 等价于内置 abs() 的封装，并确保返回类型为 float。
        - 接受所有可转换为浮点数的类型（int、float、可数值字符串等）。
        - 若输入无法转换为数值，则捕获异常并返回 None。
        - 本函数不打印错误信息，适合作为底层工具函数在数据处理中稳定使用。

    Args:
        数值 (SupportsFloat): 任意可转换为浮点数的数值类型。

    Returns:
        float | None:
            - 成功：返回绝对值（float 类型）。
            - 失败：返回 None（输入无法转换为数值时）。

    Notes:
        - 内置 abs() 对绝对值处理效率最高，本函数仅做兼容封装。
    """
    try:
        return float(abs(float(数值)))
    except Exception:
        return None
