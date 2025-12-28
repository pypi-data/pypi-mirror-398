def 删除所有Cookies(驱动器对象):
    """
    删除当前页面的所有 Cookies。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 成功返回 True，失败返回 False。
    """
    try:
        驱动器对象.delete_all_cookies()
        return True
    except Exception:
        return False