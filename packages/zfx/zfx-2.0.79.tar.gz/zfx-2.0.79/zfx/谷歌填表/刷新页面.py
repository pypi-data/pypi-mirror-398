def 刷新页面(驱动器对象):
    """
    刷新当前页面。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 成功返回 True，失败返回 False。
    """
    try:
        驱动器对象.refresh()
        return True
    except Exception:
        return False