from datetime import datetime


def 时间戳转换为时间(时间戳):
    """
    将时间戳转换为时间字符串。

    参数：
        - 时间戳：整数或字符串，单位为秒。

    返回值：
        - 成功时返回时间字符串，格式为 "YYYY-MM-DD HH:MM:SS"。
        - 如果输入格式不正确或发生异常，返回 False。

    使用示例：
        时间戳 = 1736800467
        时间字符串 = 时间戳转换为时间(时间戳)
        if 时间字符串:
            print(f"时间字符串：{时间字符串}")
        else:
            print("转换时间字符串失败。")
    """
    try:
        # 将时间戳转换为 datetime 对象
        时间对象 = datetime.fromtimestamp(int(时间戳))
        # 格式化为标准时间字符串
        时间字符串 = 时间对象.strftime("%Y-%m-%d %H:%M:%S")
        return 时间字符串
    except Exception:
        return False