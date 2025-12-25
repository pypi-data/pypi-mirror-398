def 取长度(源文本):
    """
    获取文本的长度。

    参数:
        源文本 (str): 要获取长度的文本。

    返回:
        int: 文本的长度，如果出现任何异常，则返回 -1。

    示例:
        文本 = "这是一段示例文本a"
        长度 = zfx_textutils.取长度(文本)
        print("文本的长度:", 长度)
    """
    try:
        return len(源文本)
    except Exception:  # 捕获所有异常
        return -1