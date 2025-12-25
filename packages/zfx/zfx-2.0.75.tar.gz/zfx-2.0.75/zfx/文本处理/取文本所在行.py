def 取文本所在行(源文本, 欲查找的文本, 是否区分大小写=False):
    """
    从源文本中查找文本，并返回其所在行号。

    参数:
        源文本 (str): 要搜索的源文本。
        欲查找的文本 (str): 要查找的文本。
        是否区分大小写 (bool): 是否区分大小写，默认为 False。

    返回:
        int: 查找文本所在行的行号，如果未找到文本或出现任何异常，则返回 -1。

    示例:
        文本 = "This is the fourth line"
        欲查找的文本 = "fourth"
        行号 = zfx_textutils.取文本所在行(文本, 欲查找的文本)
        print("欲查找文本所在行号:", 行号)
    """
    try:
        if not 是否区分大小写:
            源文本 = 源文本.lower()
            欲查找的文本 = 欲查找的文本.lower()

        行列表 = 源文本.splitlines()
        for 行号, 行文本 in enumerate(行列表, start=1):
            if 欲查找的文本 in 行文本:
                return 行号

        return -1
    except Exception:  # 捕获所有异常
        return -1