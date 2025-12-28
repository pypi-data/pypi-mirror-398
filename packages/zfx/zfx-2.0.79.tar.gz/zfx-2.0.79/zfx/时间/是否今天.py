from datetime import datetime


def 是否今天(时间字符串: str) -> bool:
    """
    判断指定时间是否属于今天。

    功能说明：
        - 时间格式必须为 "%Y-%m-%d %H:%M:%S"。
        - 仅比较日期部分（年月日），忽略时分秒。
        - 若输入无效或解析失败，返回 False。

    Args:
        时间字符串 (str): 待判断的时间字符串。

    Returns:
        bool: 若该时间属于今天返回 True，否则返回 False。
    """
    try:
        输入日期 = datetime.strptime(时间字符串.strip(), "%Y-%m-%d %H:%M:%S").date()
        当前日期 = datetime.now().date()
        return 输入日期 == 当前日期
    except Exception:
        return False
