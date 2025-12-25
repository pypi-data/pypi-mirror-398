from datetime import datetime


def 取系统时间():
    """
    获取当前系统时间。

    返回值：
        - 成功时返回系统时间的字符串，格式为 "YYYY-MM-DD HH:MM:SS"。
        - 如果获取失败，返回 False。

    使用示例：
        系统时间 = 取系统时间()
        if 系统时间:
            print(f"当前系统时间是：{系统时间}")
        else:
            print("获取系统时间失败。")
    """
    try:
        # 获取当前系统时间并返回默认格式
        系统时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return 系统时间
    except Exception:
        return False