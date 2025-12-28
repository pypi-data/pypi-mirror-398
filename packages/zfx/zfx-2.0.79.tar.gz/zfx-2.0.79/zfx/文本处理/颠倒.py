def 颠倒(欲转换文本, 带有中文=False):
    """
    将文本颠倒过来。

    参数:
        - 欲转换文本 (str): 欲颠倒的文本。
        - 带有中文 (bool): 如果为 True，则假定文本中包含中文字符。

    返回:
        - str: 颠倒后的文本。如果转换失败或出现任何异常，则返回 False。

    示例:
        文本 = "123456"
        结果 = zfx_textutils.颠倒(文本)
        print(结果)  # 输出：654321
    """
    try:
        if 带有中文:
            return 欲转换文本[::-1]
        else:
            # 如果文本中含有中文字符，直接使用[::-1]可能会出现乱序，所以先转换为列表再逆序
            文本列表 = list(欲转换文本)
            文本列表.reverse()
            return ''.join(文本列表)
    except Exception:  # 捕获所有异常
        return False