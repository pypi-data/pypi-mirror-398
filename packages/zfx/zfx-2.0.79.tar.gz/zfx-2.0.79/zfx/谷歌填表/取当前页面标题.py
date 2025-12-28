def 取当前页面标题(驱动器对象):
    """
    获取当前页面的标题。

    参数：
        - 驱动器对象: 浏览器驱动对象

    返回值：
        - 当前页面的标题，如果发生错误，返回空字符串
    """
    try:
        return 驱动器对象.title
    except Exception:
        return ""