import pyperclip


def 取剪辑版内容():
    """
    获取系统剪辑板的内容。

    返回:
        str: 系统剪辑板的内容。如果获取失败，则返回 None。

    使用示例:
        剪辑版内容 = 系统_取剪辑版内容()
        print("剪辑版内容:", 剪辑版内容)
    """

    try:
        剪辑版内容 = pyperclip.paste()
        return 剪辑版内容
    except Exception:
        return None