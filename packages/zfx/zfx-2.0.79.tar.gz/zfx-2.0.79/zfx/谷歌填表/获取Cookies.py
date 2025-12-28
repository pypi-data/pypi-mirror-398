def 获取Cookies(驱动器对象):
    """
    获取当前页面的所有 Cookies。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 返回一个包含所有 Cookie 的列表，成功时返回列表，失败返回 None。
    """
    try:
        # 获取所有 Cookies
        cookies = 驱动器对象.get_cookies()
        return cookies  # 成功返回 Cookies 列表
    except Exception:
        return None  # 发生异常时返回 None