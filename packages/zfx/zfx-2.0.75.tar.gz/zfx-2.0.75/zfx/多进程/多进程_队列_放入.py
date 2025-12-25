def 多进程_队列_放入(多进程队列对象, 元素, 超时=None):
    """
    将元素放入多进程队列中。

    参数：
        - 多进程队列对象: 多进程队列对象
        - 元素: 要放入队列的元素
        - 超时（int）: 等待时间（秒），默认为None表示无限等待

    返回：
        - True 如果成功放入队列
        - False 如果放入失败
    """
    try:
        多进程队列对象.put(元素, timeout=超时)
        return True
    except Exception:
        return False