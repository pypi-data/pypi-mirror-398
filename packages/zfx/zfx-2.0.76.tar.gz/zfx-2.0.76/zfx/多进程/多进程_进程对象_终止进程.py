def 多进程_进程对象_终止进程(进程对象):
    """
    终止一个运行中的进程。

    参数：
        - 进程对象：需要终止的进程对象

    返回：
        - True 如果成功终止进程
        - False 如果终止进程失败或进程对象无效
    """
    try:
        if 进程对象.is_alive():
            进程对象.terminate()
            进程对象.join()  # 等待子进程正确终止
        return True
    except Exception:
        return False