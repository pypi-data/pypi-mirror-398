def 到大写(要转换的文本):
    """
    将文本转换为大写。

    参数:
        - 要转换的文本 (str): 要转换为大写的文本。

    返回:
        - str: 转换为大写的文本。如果输入无效，则返回 False。

    示例:
        文本 = "Hello world"
        结果 = 到大写(文本)
        print(结果)  # 输出：HELLO WORLD
    """
    # 检查输入是否为字符串
    if not isinstance(要转换的文本, str):
        return False

    # 返回转换为大写的文本
    return 要转换的文本.upper()
