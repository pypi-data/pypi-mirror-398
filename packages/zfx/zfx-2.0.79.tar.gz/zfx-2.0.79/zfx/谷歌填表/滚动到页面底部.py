def 滚动到页面底部(驱动器对象):
    """
    滚动到页面底部。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 成功返回 True，失败返回 False。
    """
    try:
        驱动器对象.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        return True
    except Exception:
        return False