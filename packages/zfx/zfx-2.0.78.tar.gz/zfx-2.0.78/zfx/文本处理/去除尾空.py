def 去除尾空(文本):
    """
    去除文本结尾的空格。

    参数:
        - 文本 (str): 要去除结尾空格的文本。

    返回:
        - str: 去除结尾空格的文本。如果输入不是字符串，则返回 False。

    示例:
        文本 = "Hello world   "
        结果 = 去除尾空(文本)
        print(结果)  # 输出："Hello world"
    """
    if not isinstance(文本, str):
        return False

    return 文本.rstrip()
