def 取出现次数(被搜索文本, 欲搜索文本, 是否区分大小写=False):
    """
    计算文本中某子串出现的次数。

    参数:
        被搜索文本 (str): 要搜索的原始文本。
        欲搜索文本 (str): 要搜索的子串文本。
        是否区分大小写 (bool): 是否区分大小写，默认为 False。

    返回:
        int: 搜索文本在被搜索文本中出现的次数。如果出现任何异常，则返回 False。

    示例:
        文本 = "This is a sample text. This text is for demonstration purposes."
        搜索文本 = "Text"
        出现次数 = zfx_textutils.取出现次数(文本, 搜索文本)
        print("搜索文本出现的次数:", 出现次数)
    """
    try:
        if not 是否区分大小写:
            被搜索文本 = 被搜索文本.lower()
            欲搜索文本 = 欲搜索文本.lower()

        return 被搜索文本.count(欲搜索文本)
    except Exception:  # 捕获所有异常
        return False