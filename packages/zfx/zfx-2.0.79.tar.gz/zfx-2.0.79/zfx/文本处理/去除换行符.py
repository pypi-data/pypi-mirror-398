def 去除换行符(文本):
    """
    去除字符串中的所有换行符。

    参数:
        - 文本 (str): 输入的字符串。

    返回:
        - str: 去除换行符后的字符串。如果输入不是字符串，将其转换为字符串后处理。发生异常则返回空字符串。
    """
    try:
        # 确保输入是字符串类型
        if not isinstance(文本, str):
            文本 = str(文本)

        return 文本.replace('\n', '').replace('\r', '')
    except Exception:
        return ""