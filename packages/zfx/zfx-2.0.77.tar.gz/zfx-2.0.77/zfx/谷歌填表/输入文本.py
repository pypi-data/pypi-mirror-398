def 输入文本(元素对象, 文本):
    """
    向指定的元素输入文本。使用 send_keys 方法输入文本

    参数：
        - 元素对象: 已获取的网页元素对象（如输入框）。
        - 文本: 要输入的文本内容。

    返回值：
        - 成功返回 True，失败返回 False。
    """
    try:
        元素对象.send_keys(文本)
        return True  # 成功返回 True
    except Exception:
        return False  # 发生异常时返回 False