def 从左往右取(字符串, 字符数量):
    """
    从字符串的左侧开始提取指定数量的字符。

    参数:
        - 字符串 (str): 输入的字符串。
        - 字符数量 (int): 要提取的字符数量。

    返回:
        - str: 从左侧提取的字符。如果字符数量大于字符串长度，则返回整个字符串。
        - bool: 如果出现异常，返回 False。
    """
    try:
        if not isinstance(字符串, str) or not isinstance(字符数量, int):
            return False

        if 字符数量 < 0:
            return False

        return 字符串[:字符数量]
    except Exception:
        return False