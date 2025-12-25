import multiprocessing


def 多进程_启动进程(目标函数, 元组参数):
    """
    启动一个新的进程并返回进程对象。

    参数：
        - 执行体：要在子进程中运行的函数
        - 参数传递：传递给函数的参数，必须是元组形式

    返回：
        - 进程对象，如果进程启动失败则返回 None

    使用例程：
    if __name__ == "__main__":
        进程对象 = 进程_启动进程(目标函数, (队列对象,"123",456))

    小提示：
    程序必需要在保护块下进行启动，否则会出现无限递归问题导致异常,元组成员数有多少个，目标函数接收的参数就应该有多少个
    """
    try:
        # 创建一个进程
        p = multiprocessing.Process(target=目标函数, args=元组参数)

        # 启动进程
        p.start()

        return p
    except Exception:
        return None
