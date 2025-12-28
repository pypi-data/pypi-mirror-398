import multiprocessing


def 多进程_进程对象_取名称():
    """
    返回当前进程的名称。

    返回：
        - 当前进程的名称 (字符串)
        - 如果获取失败，返回 None
    """
    try:
        return multiprocessing.current_process().name
    except Exception:
        return None