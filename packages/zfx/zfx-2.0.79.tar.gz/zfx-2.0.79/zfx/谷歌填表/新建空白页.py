def 新建空白页(驱动器对象, 切换到新标签页=False):
    """
    新建一个空白标签页，并根据用户选择决定是否切换到该标签页。

    参数：
        - 驱动器对象: 浏览器驱动对象。
        - 切换到新标签页: 布尔值，默认为 False。为 True 时切换到新建的标签页。

    返回值：
        - 成功返回 True。
        - 失败返回 False。
    """
    try:
        # 使用 JavaScript 打开一个新的空白标签页
        驱动器对象.execute_script("window.open('about:blank', '_blank');")

        # 如果用户选择切换到新标签页，则切换到最新打开的标签页
        if 切换到新标签页:
            驱动器对象.switch_to.window(驱动器对象.window_handles[-1])

        return True
    except Exception:
        return False