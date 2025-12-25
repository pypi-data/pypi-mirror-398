from datetime import datetime


def 获取时间间隔秒数(开始时间, 结束时间):
    """
    计算两个时间点之间的时间间隔，以秒为单位。

    参数：
        - 开始时间：字符串，格式为 "YYYY-MM-DD HH:MM:SS"。
        - 结束时间：字符串，格式为 "YYYY-MM-DD HH:MM:SS"。

    返回值：
        - 成功时返回时间间隔的秒数（整数）。
        - 如果输入格式不正确或发生异常，返回 False。

    使用示例：
        开始时间 = "2025-01-13 22:34:27"
        结束时间 = "2024-05-13 23:34:27"
        间隔秒数 = 获取时间间隔秒数(开始时间, 结束时间)
        if 间隔秒数:
            print(f"时间间隔：{间隔秒数} 秒")
        else:
            print("计算时间间隔失败。")
    """
    try:
        # 将时间字符串解析为 datetime 对象
        开始 = datetime.strptime(开始时间, "%Y-%m-%d %H:%M:%S")
        结束 = datetime.strptime(结束时间, "%Y-%m-%d %H:%M:%S")

        # 计算时间差并返回秒数（绝对值）
        时间间隔秒数 = abs((结束 - 开始).total_seconds())
        return int(时间间隔秒数)
    except Exception:
        return False
