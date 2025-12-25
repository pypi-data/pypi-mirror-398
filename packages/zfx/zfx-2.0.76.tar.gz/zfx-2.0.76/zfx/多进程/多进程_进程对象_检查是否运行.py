def 多进程_进程对象_检查是否运行(进程对象):
    """
    检查进程对象是否仍在运行。

    参数：
        - 进程对象：需要检查的进程对象

    返回：
        - True 如果进程正在运行
        - False 如果进程未运行或检查失败
    """
    try:
        return 进程对象.is_alive()
    except Exception:
        return False