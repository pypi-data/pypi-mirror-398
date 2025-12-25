def 关闭当前标签页(驱动器对象):
    """
    关闭当前标签页。

    参数：
        - 驱动器对象: 浏览器驱动对象

    返回值：
        - 成功返回 True
        - 失败返回 False
    """
    try:
        驱动器对象.close()
        return True
    except Exception:
        return False