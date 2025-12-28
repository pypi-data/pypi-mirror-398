from datetime import datetime


def 取星期几(时间字符串: str | None = None) -> str:
    """
    获取指定时间或当前时间的星期几。

    功能说明：
        - 若未传入时间字符串，则默认取当前系统时间。
        - 时间格式需为 "%Y-%m-%d %H:%M:%S"。
        - 返回结果为中文，如 "星期一"、"星期日"。
        - 若输入格式错误，返回空字符串 ""。

    Args:
        时间字符串 (str | None): 可选，指定的时间字符串。
                                 为空时默认使用当前时间。

    Returns:
        str: 对应的中文星期字符串，出错时返回空字符串。
    """
    try:
        if 时间字符串:
            时间对象 = datetime.strptime(时间字符串.strip(), "%Y-%m-%d %H:%M:%S")
        else:
            时间对象 = datetime.now()

        星期列表 = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return 星期列表[时间对象.weekday()]
    except Exception:
        return ""
