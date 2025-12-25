import threading
from typing import Callable, Any


def 启动线程(目标函数: Callable[..., Any], *参数, 守护线程: bool = True) -> threading.Thread:
    """
    启动一个新的线程来执行指定函数。

    功能说明：
        帮你“开一个分身”去做事（下载、发请求、打印日志等）。
        主程序不会等待它完成，会继续往下跑。

    Args:
        目标函数 (Callable[..., Any]):
            新线程里要执行的函数，例如 下载任务、打印日志 等。

        *参数:
            传给目标函数的位置参数。
            示例：启动线程(下载任务, "https://example.com", 3)

        守护线程 (bool):
            是否让线程随主程序一起结束。
            - True：主程序一结束，不管线程做完没做完，直接退出（适合后台监听/心跳这类非关键任务）。
            - False：主程序会等待线程执行完再结束（适合必须完成的任务，如写文件、落库）。

    Returns:
        threading.Thread:
            已启动的线程对象，可用于：
            - is_alive()：查看是否仍在运行
            - join()：等待线程结束

    注意事项：
        - 守护线程=True 时，线程不会阻止程序退出，可能来不及执行 finally/with 收尾。
        - 非守护线程里若写了死循环且没有退出条件，程序将一直不结束。
        - 需要确保“必须完成”的操作（写盘/数据库）请设为守护线程=False，并在退出前 join()。

    简要用法（非交互示例）：
        def 打印编号(n):
            print(f"线程 {n} 开始")
            time.sleep(1)
            print(f"线程 {n} 结束")

        for i in range(3):
            启动线程(打印编号, i)
        # 主程序会继续往下执行，不会等待上面的线程结束
    """
    线程 = threading.Thread(target=目标函数, args=参数)
    线程.daemon = 守护线程
    线程.start()
    return 线程
