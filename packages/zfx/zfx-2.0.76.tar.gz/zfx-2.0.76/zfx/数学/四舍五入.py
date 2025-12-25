from typing import SupportsFloat, Optional


def 四舍五入(数值: SupportsFloat, 小数位数: int = 0) -> Optional[float]:
    """
    对数值执行四舍五入，并保留指定的小数位数。

    功能说明：
        - 基于 Python 内置 round() 实现四舍五入。
        - 支持所有可转换为浮点数的类型，例如 int、float、可数值字符串等。
        - 当小数位数为 0 时，返回值仍为 float 类型（例如 3 → 3.0）。
        - 若输入无法转换为 float，返回 None 而不是抛出异常。
        - 注意：round() 使用“银行家舍入”（即 round half to even），
          与传统的 ROUND_HALF_UP 不完全相同。

    Args:
        数值 (SupportsFloat): 需要四舍五入的数值。
        小数位数 (int): 保留的小数位数，默认为 0。

    Returns:
        float | None:
            - 成功：返回四舍五入后的浮点数。
            - 失败：返回 None（例如输入非法、无法转换为数值）。

    Notes:
        - 若需要金融行业常用的传统四舍五入规则（ROUND_HALF_UP），
          应使用 Decimal.quantize，而不是 round()。
    """
    try:
        return float(round(float(数值), 小数位数))
    except Exception:
        return None
