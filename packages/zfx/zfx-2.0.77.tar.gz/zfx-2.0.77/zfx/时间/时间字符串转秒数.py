def 时间字符串转秒数(时间字符串: str) -> int | None:
    """
    将 "HH:MM:SS" 格式的时间字符串转换为总秒数。

    功能说明：
        - 若格式不正确或含非法字符，返回 None。
        - 常用于解析持续时间或计算时间差。

    Args:
        时间字符串 (str): 时间字符串，格式必须为 "HH:MM:SS"。

    Returns:
        int | None: 总秒数；若格式无效返回 None。
    """
    try:
        时, 分, 秒 = map(int, 时间字符串.strip().split(":"))
        return 时 * 3600 + 分 * 60 + 秒
    except Exception:
        return None
