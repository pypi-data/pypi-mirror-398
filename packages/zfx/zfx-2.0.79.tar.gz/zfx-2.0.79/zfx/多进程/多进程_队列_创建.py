import multiprocessing


def 多进程_队列_创建(最大容量=0):
    """
    创建并返回一个新的多进程队列对象。

    参数：
        - 最大容量（int）: 队列的最大容量。默认为0，表示无限容量。

    返回：
        - 多进程队列对象，如果创建成功
        - None，如果创建失败
    """
    try:
        queue = multiprocessing.Queue(maxsize=int(最大容量))
        return queue
    except Exception:
        return None