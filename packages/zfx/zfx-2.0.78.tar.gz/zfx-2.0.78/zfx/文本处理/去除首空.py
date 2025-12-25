def 去除首空(文本):
    """
    去除文本开头的空格。

    参数:
        - 文本 (str): 要去除开头空格的文本。

    返回:
        - str: 去除开头空格的文本。如果转换失败或出现任何异常，则返回 False。

    示例:
        文本 = "   Hello world"
        结果 = zfx_textutils.去除首空(文本)
        print(结果)  # 输出："Hello world"
    """
    try:
        去除首空文本 = 文本.lstrip()
        return 去除首空文本
    except Exception:  # 捕获所有异常
        return False