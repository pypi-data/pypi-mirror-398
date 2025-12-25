def 截图并保存(驱动器对象, 文件路径):
    """
    对当前页面截图并保存为文件。

    参数：
        - 驱动器对象: 浏览器驱动对象。
        - 文件路径: 保存截图的文件路径（包括文件名和扩展名，如 'screenshot.png'）。

    返回值：
        - 成功返回 True，失败返回 False。
    """
    try:
        # 截图并保存到指定路径
        驱动器对象.save_screenshot(文件路径)
        return True
    except Exception:
        return False  # 发生异常时返回 False