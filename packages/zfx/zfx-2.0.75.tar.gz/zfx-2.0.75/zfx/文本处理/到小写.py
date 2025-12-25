def 到小写(要转换的文本):
    """
    将文本转换为小写。

    参数:
        要转换的文本 (str): 要转换为小写的文本。

    返回:
        str: 转换为小写的文本。如果输入不是字符串，则返回 False。

    示例:
        文本 = "Hello World"
        结果 = 到小写(文本)
        print(结果)  # 输出：hello world
    """
    if not isinstance(要转换的文本, str):
        return False

    return 要转换的文本.lower()
