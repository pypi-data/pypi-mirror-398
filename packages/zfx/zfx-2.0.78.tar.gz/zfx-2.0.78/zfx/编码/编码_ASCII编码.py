def 编码_ASCII编码(字符串):
    """
    对字符串进行 ASCII 编码。

    参数:
        - 字符串 (str): 要进行编码的字符串。

    返回:
        - 编码后的 ASCII 码列表 (list)。失败则返回 None
    """
    try:
        编码后的列表 = [ord(char) for char in 字符串]
        return 编码后的列表
    except Exception:
        return None