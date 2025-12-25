def 切换标签页(驱动器对象, 索引):
    """
    切换到指定的标签页。

    参数：
        - 驱动器对象: 浏览器驱动对象。
        - 索引: 标签页的索引，类型为整数，索引从 0 开始。

    返回值：
        - 成功返回 True。
        - 失败返回 False。
    """
    try:
        # 获取所有标签页的句柄
        handles = 驱动器对象.window_handles

        # 检查索引是否合法
        if 索引 < 0 or 索引 >= len(handles):
            raise IndexError("索引超出范围")

        # 切换到指定的标签页
        驱动器对象.switch_to.window(handles[索引])

        return True
    except Exception:
        return False