def 只取汉字(字符串):
    """
    从文本中提取汉字。

    参数:
        字符串 (str): 要从中提取汉字的文本。

    返回:
        str: 提取出的汉字文本。如果出现任何异常，则返回 False。

    示例:
        文本 = "这是一段中文文本，English words are also included."
        汉字文本 = zfx_textutils.只取汉字(文本)
        print("取出的汉字文本:", 汉字文本)
    """
    try:
        汉字列表 = [char for char in 字符串 if '\u4e00' <= char <= '\u9fff']
        return ''.join(汉字列表)
    except Exception:  # 捕获所有异常
        return False