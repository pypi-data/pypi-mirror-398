from datetime import datetime


def 获取今日剩余时长(返回类型: int = 1, 精确到毫秒: bool = False) -> float:
    """
    计算当前距离今日结束（23:59:59）所剩的时间长度。

    功能说明：
        根据系统当前时间计算今日剩余时长，并按指定单位返回。
        常用于倒计时、任务计划、日志统计等场景。

    Args:
        返回类型 (int): 输出单位类型。0=秒，1=分钟（默认），2=小时。
        精确到毫秒 (bool): 是否保留小数部分。False（默认）返回整数，True 返回浮点数。

    Returns:
        float: 今日剩余时长，单位由“返回类型”决定。异常或参数不合法时返回 0.0。

    Notes:
        - 使用本地系统时间与本地时区。
        - 不抛出异常，所有异常统一吞掉并返回 0.0。
    """
    try:
        当前时间 = datetime.now()
        今日结束 = datetime.combine(当前时间.date(), datetime.max.time()).replace(microsecond=0)
        剩余秒数 = (今日结束 - 当前时间).total_seconds()

        if not 精确到毫秒:
            剩余秒数 = int(剩余秒数)

        if 返回类型 == 0:
            return float(剩余秒数)
        if 返回类型 == 1:
            return float(剩余秒数) / 60
        if 返回类型 == 2:
            return float(剩余秒数) / 3600
        return 0.0
    except Exception:
        return 0.0
