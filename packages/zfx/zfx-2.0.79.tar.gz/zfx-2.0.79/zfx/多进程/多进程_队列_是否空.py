def 多进程_队列_是否空(多进程队列对象):
    """
    检查多进程队列是否为空。

    参数：
        - 多进程队列对象: 多进程队列对象

    返回：
        - True 如果队列为空
        - False 如果队列不为空或发生异常
    """
    try:
        return 多进程队列对象.empty()
    except Exception:
        return False