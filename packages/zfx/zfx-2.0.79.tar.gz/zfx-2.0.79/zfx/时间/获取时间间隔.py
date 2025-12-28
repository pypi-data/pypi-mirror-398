from datetime import datetime


def 获取时间间隔(时间1: str, 时间2: str, 单位: int = 1) -> float | None:
    """
    计算两个时间之间的间隔，并按指定单位返回结果。

    功能说明：
        - 时间格式必须为 "%Y-%m-%d %H:%M:%S"。
        - 单位参数定义如下：
            0 → 毫秒
            1 → 秒（默认）
            2 → 分钟
            3 → 小时
        - 若格式错误或计算异常，返回 None。

    Args:
        时间1 (str): 起始时间字符串。
        时间2 (str): 结束时间字符串。
        单位 (int): 返回结果的单位（0=毫秒, 1=秒, 2=分, 3=小时）。

    Returns:
        float | None: 两个时间的间隔值；出错时返回 None。
    """
    try:
        t1 = datetime.strptime(时间1.strip(), "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(时间2.strip(), "%Y-%m-%d %H:%M:%S")
        秒差 = (t2 - t1).total_seconds()

        match 单位:
            case 0:
                return 秒差 * 1000
            case 1:
                return 秒差
            case 2:
                return 秒差 / 60
            case 3:
                return 秒差 / 3600
            case _:
                return None
    except Exception:
        return None

