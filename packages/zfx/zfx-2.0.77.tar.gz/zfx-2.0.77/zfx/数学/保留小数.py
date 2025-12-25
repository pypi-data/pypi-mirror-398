from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, SupportsFloat


def 保留小数(数值: SupportsFloat, 位数: int) -> Optional[float]:
    """
    将数值保留至指定的小数位数（四舍五入）。

    功能说明：
        - 使用 Decimal 执行精确浮点运算，避免二进制浮点误差。
        - 默认采用“四舍五入”策略（ROUND_HALF_UP），与金融行业常用规则一致。
        - 若输入数值无法转换、或位数非法，则返回 None。
        - 全程不抛出异常，适用于数据处理、爬虫、解析转换等稳定性要求较高的场景。

    Args:
        数值 (SupportsFloat): 需要处理的数值。可为 int、float、Decimal 或可转换为数值的字符串。
        位数 (int): 小数位数，必须为非负整数。

    Returns:
        float | None:
            - 成功：返回保留指定位数后的新浮点数。
            - 失败：返回 None（如位数为负或输入格式非法）。

    Notes:
        - 本函数使用 Decimal('1.00...') 作为量化模板实现精确四舍五入。
        - 若需银行家舍入（Round half to even），应另行使用 round() 函数。

    """
    try:
        if 位数 < 0:
            return None

        # 使用 Decimal 保证精确运算
        dec_value = Decimal(str(数值))
        模板 = Decimal("1." + ("0" * 位数))  # 例如 "1.00"

        结果 = dec_value.quantize(模板, rounding=ROUND_HALF_UP)
        return float(结果)

    except Exception:
        return None