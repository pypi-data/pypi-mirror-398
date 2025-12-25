from datetime import datetime


def 取系统时间戳():
    """
    获取当前系统时间的时间戳。

    返回值：
        - 成功时返回时间戳（整数，单位为秒）。
        - 如果获取失败，返回 False。

    使用示例：
        系统时间戳 = 取系统时间戳()
        if 系统时间戳:
            print(f"当前系统时间戳：{系统时间戳}")
        else:
            print("获取系统时间戳失败。")
    """
    try:
        # 获取当前系统时间并转换为时间戳
        当前时间戳 = int(datetime.now().timestamp())
        return 当前时间戳
    except Exception:
        return False