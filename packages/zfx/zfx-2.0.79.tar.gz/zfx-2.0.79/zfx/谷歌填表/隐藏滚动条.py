def 隐藏滚动条(驱动器对象):
    """
    使用 JavaScript 隐藏页面的滚动条。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 成功返回 True，表示滚动条已被隐藏。
        - 如果发生异常，返回 False。
    """
    try:
        # 使用 JavaScript 隐藏滚动条
        驱动器对象.execute_script("document.body.style.overflow = 'hidden';")
        return True  # 操作成功返回 True
    except Exception:
        return False  # 操作失败返回 False