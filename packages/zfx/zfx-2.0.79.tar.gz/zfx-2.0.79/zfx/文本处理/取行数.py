def 取行数(文本):
    """
    统计文本的行数。

    参数:
        - 文本 (str): 要统计行数的文本。

    返回:
        int: 文本的行数，如果出现任何异常，则返回 -1。

    示例:
        文本 = "这是第一行"
        行数 = zfx_textutils.取行数(文本)
        print("文本共有", 行数, "行")
    """
    try:
        行数 = len(文本.splitlines())
        return 行数
    except Exception:  # 捕获所有异常
        return -1