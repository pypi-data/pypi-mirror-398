from datetime import datetime


def 时间转换为时间戳(时间字符串):
    """
    将时间字符串转换为时间戳。

    参数：
        - 时间字符串：字符串，格式为 "YYYY-MM-DD HH:MM:SS"。

    返回值：
        - 成功时返回时间戳（整数，单位为秒）。
        - 如果输入格式不正确或发生异常，返回 False。

    使用示例：
        时间字符串 = "2025-01-13 22:34:27"
        时间戳 = 时间转换为时间戳(时间字符串)
        if 时间戳:
            print(f"时间戳：{时间戳}")
        else:
            print("转换时间戳失败。")
    """
    try:
        # 将时间字符串解析为 datetime 对象
        时间对象 = datetime.strptime(时间字符串, "%Y-%m-%d %H:%M:%S")
        # 转换为时间戳（秒）
        时间戳 = int(时间对象.timestamp())
        return 时间戳
    except Exception:
        return False