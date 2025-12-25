def 取当前页面网址(驱动器对象):
    """
    获取当前页面的URL地址。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 返回当前页面的URL字符串。
    """
    try:
        # 获取当前页面的URL
        当前网址 = 驱动器对象.current_url
        return 当前网址
    except Exception:
        return None  # 发生异常时返回 None