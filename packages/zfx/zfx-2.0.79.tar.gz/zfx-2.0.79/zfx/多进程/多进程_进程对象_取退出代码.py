def 多进程_进程对象_取退出代码(进程对象):
    """
    返回进程对象的退出代码。

    参数：
        - 进程对象：需要获取退出代码的进程对象

    返回：
        - 进程对象的退出代码，如果获取成功
        - None，如果获取失败
    """
    try:
        return 进程对象.exitcode
    except Exception:
        return None