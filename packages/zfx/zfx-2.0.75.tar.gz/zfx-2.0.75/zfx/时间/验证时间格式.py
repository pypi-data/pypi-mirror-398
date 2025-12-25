from datetime import datetime


def 验证时间格式(时间字符串: str, 格式: str = "%Y-%m-%d %H:%M:%S") -> bool:
    """
    验证给定时间字符串是否符合指定格式。

    功能说明：
        - 默认格式为 "%Y-%m-%d %H:%M:%S"（例如 "2025-11-12 17:47:34"）。
        - 若验证通过返回 True，否则返回 False。
        - 内部使用 datetime.strptime() 检查，不依赖第三方库。

    Args:
        时间字符串 (str): 待验证的时间字符串。
        格式 (str): 期望的时间格式，默认为 "%Y-%m-%d %H:%M:%S"。

    Returns:
        bool: 若格式正确返回 True；否则返回 False。
    """
    try:
        datetime.strptime(时间字符串.strip(), 格式)
        return True
    except Exception:
        return False