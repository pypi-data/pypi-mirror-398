def 从中间往左取(字符串, 开始位置, 字符数量):
    """
    从字符串的指定开始位置向左提取指定数量的字符。

    参数:
        - 字符串 (str): 输入的字符串。
        - 开始位置 (int): 开始提取的起始位置（从0开始）。
        - 字符数量 (int): 要提取的字符数量。

    返回:
        - str: 从指定位置向左提取的字符。如果字符数量大于开始位置，则返回从字符串开头到开始位置的所有字符。
        - bool: 如果出现异常，返回 False。
    """
    try:
        if not isinstance(字符串, str) or not isinstance(开始位置, int) or not isinstance(字符数量, int):
            return False

        if 开始位置 < 0 or 字符数量 < 0 or 开始位置 >= len(字符串):
            return False

        return 字符串[max(0, 开始位置 - 字符数量):开始位置]
    except Exception:
        return False