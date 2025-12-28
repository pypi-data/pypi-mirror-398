def 判断页面是否加载完毕(驱动器对象):
    """
    判断当前页面是否完全加载完毕。

    参数：
        - 驱动器对象: 浏览器驱动对象。

    返回值：
        - 如果页面加载完毕返回 True，未加载完毕返回 False。
    """
    try:
        # 执行 JavaScript 检查 document.readyState 是否为 complete
        页面状态 = 驱动器对象.execute_script("return document.readyState")
        return 页面状态 == "complete"
    except Exception:
        return False  # 发生异常时返回 False