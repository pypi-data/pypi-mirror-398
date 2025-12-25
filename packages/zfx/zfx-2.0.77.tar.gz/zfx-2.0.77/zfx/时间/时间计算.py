from datetime import datetime, timedelta


def 时间计算(时间字符串: str, 秒数: int) -> str | None:
    """
    在指定时间基础上增加（或减少）指定秒数，并返回新的时间字符串。

    功能说明：
        - 适用于格式 "YYYY-MM-DD HH:MM:SS"（例如 "2025-11-12 17:47:34"）。
        - 秒数可为负值（表示向前推）。
        - 若输入格式无效或计算出错，返回 None。

    Args:
        时间字符串 (str): 原始时间字符串。
        秒数 (int): 要增加的秒数，负数表示向前。

    Returns:
        str | None: 成功返回计算后的时间字符串；失败返回 None。
    """
    try:
        原时间 = datetime.strptime(时间字符串.strip(), "%Y-%m-%d %H:%M:%S")
        新时间 = 原时间 + timedelta(seconds=秒数)
        return 新时间.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
