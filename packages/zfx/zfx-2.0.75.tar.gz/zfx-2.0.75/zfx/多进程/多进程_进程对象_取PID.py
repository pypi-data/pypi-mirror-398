def 多进程_进程对象_取PID(进程对象):
    """
    返回进程对象的PID。

    参数：
        - 进程对象：需要获取PID的进程对象

    返回：
        - 进程对象的PID，如果获取成功
        - None，如果获取失败
    """
    try:
        return 进程对象.pid
    except Exception:
        return None