def 多进程_队列_是否满(多进程队列对象):
    """
    检查多进程队列是否已满。

    参数：
        - 多进程队列对象: 多进程队列对象

    返回：
        - True 如果队列已满
        - False 如果队列未满或发生异常
    """
    try:
        return 多进程队列对象.full()
    except Exception:
        return False