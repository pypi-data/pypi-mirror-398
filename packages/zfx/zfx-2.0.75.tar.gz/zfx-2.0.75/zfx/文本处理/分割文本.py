def 分割文本(待分割文本, 分隔符):
    """
    将文本按照指定分隔符分割。

    参数:
        - 待分割文本 (str): 要分割的文本。
        - 分隔符 (str): 分隔文本的字符串。

    返回:
        - list: 分割后的文本列表。如果输入无效，则返回 False。

    示例:
        文本 = "apple,orange,banana"
        分隔符 = ","
        分割结果 = 分割文本(文本, 分隔符)
        print("分割结果:", 分割结果)
    """
    # 检查输入类型
    if not isinstance(待分割文本, str) or not isinstance(分隔符, str):
        return False

    # 正常执行分割
    return 待分割文本.split(分隔符)