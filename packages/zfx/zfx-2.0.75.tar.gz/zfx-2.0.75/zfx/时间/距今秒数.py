from datetime import datetime


def 距今秒数(时间字符串: str) -> float | None:
    """
    计算给定时间距当前系统时间的秒数（未来为正，过去为负）。

    功能说明：
        - 时间格式必须为 "%Y-%m-%d %H:%M:%S"。
        - 若输入格式无效或计算异常，返回 None。
        - 适用于判断任务剩余时间、延迟检测、定时器等场景。

    Args:
        时间字符串 (str): 目标时间字符串。

    Returns:
        float | None: 与当前时间的秒数差值（t_目标 - t_当前），
                      出错时返回 None。
    """
    try:
        给定时间 = datetime.strptime(时间字符串.strip(), "%Y-%m-%d %H:%M:%S")
        当前时间 = datetime.now()
        return (给定时间 - 当前时间).total_seconds()
    except Exception:
        return None