import platform


def 取CPU型号() -> str:
    """
    获取电脑CPU型号。

    返回:
        str: CPU型号。如果获取失败，则返回空字符串。

    使用示例:
        cpu型号 = 系统_取CPU型号()
        print("CPU型号：", cpu型号)
    """
    try:
        return platform.processor()
    except Exception:
        return ""