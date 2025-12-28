def 取网页源码(驱动器对象):
    """
    获取当前页面的网页源码。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 返回当前页面的HTML源码字符串。
    """
    try:
        # 获取当前页面的源码
        网页源码 = 驱动器对象.page_source
        return 网页源码
    except Exception:
        return None  # 发生异常时返回 None