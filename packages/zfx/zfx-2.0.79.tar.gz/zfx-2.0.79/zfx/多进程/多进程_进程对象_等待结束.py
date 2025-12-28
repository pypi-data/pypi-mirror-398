def 多进程_进程对象_等待结束(进程对象, 超时=None):
    """
    等待进程对象结束。

    参数：
        - 进程对象：需要等待的进程对象
        - 超时：等待的最大时间（以秒为单位）。默认为None，表示无限等待。

    返回：
        - True 如果进程成功结束
        - False 如果等待失败或超时
    """
    try:
        进程对象.join(timeout=超时)
        if 进程对象.is_alive():
            return False
        return True
    except Exception:
        return False