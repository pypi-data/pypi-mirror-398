def 滚动到元素所在处(驱动器对象, 元素对象):
    """
    滚动页面，使指定的元素位于可见区域。

    参数：
        - 驱动器对象: 浏览器驱动对象。
        - 元素对象: 需要滚动到的元素对象。

    返回值：
        - 成功返回 True。
        - 失败返回 False。
    """
    try:
        # 使用 JavaScript 滚动到元素位置
        驱动器对象.execute_script("arguments[0].scrollIntoView();", 元素对象)
        return True
    except Exception:
        return False  # 发生异常时返回 False