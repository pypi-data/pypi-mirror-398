import datetime


def 取系统现行时间():
    """
    获取系统当前时间。

    无需传递参数。

    返回:
        str: 格式化后的当前时间字符串，格式为 "%Y-%m-%d %H:%M:%S"。如果获取失败，则返回空字符串。

    使用示例:
        系统时间 = 系统_取系统现行时间()
        print(系统时间)
    """
    try:
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_time
    except Exception:
        return ""