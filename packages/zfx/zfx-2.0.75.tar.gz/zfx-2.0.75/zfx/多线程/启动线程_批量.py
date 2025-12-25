import threading
from typing import Callable, Any, Iterable, List, Tuple


def 启动线程_批量(
    目标函数: Callable[..., Any],
    参数序列: Iterable[Tuple[Any, ...]],
    守护线程: bool = True
) -> List[threading.Thread]:
    """
    批量启动多个线程，让同一个函数并发执行不同参数。

    功能说明：
        一次性为同一目标函数创建并启动多个线程。
        常用于批量下载、批量发请求、并发处理任务等场景。
        函数会立即返回所有线程对象，主程序可选择是否 join 等待。

    Args:
        目标函数 (Callable[..., Any]):
            每个线程要执行的函数。

        参数序列 (Iterable[Tuple[Any, ...]]):
            每个线程对应的一组参数，建议使用“元组”逐项提供。
            若某项不是元组，会自动包装为单元素元组。
            例如：[("A", 1), ("B", 2)] 将分别执行：
                目标函数("A", 1)
                目标函数("B", 2)

        守护线程 (bool):
            是否将所有线程设置为守护线程。
            - True：主程序结束时不等待这些线程，直接退出（适合后台类任务）。
            - False：主程序会在退出前等待这些线程结束（可手动调用 join）。

    Returns:
        List[threading.Thread]:
            所有已启动的线程对象，可用于：
            - is_alive()：查看运行状态
            - join()：等待该线程结束

    注意事项：
        - 本函数不做异常捕获；若需要屏蔽错误，可在目标函数内部使用 try/except。
        - 当“守护线程=True”时，线程可能来不及执行清理逻辑（如文件 flush、数据库提交）。
        - 若任务可能是死循环或常驻线程，请设置“守护线程=True”，否则主程序将无法退出。

    用法示例（非交互）：
        def 任务(名称: str, 秒: int):
            print(f"{名称} 开始")
            time.sleep(秒)
            print(f"{名称} 结束")

        线程对象列表 = 启动线程_批量(
            目标函数=任务,
            参数序列=[("任务1", 1), ("任务2", 2), ("任务3", 3)],
            守护线程=False
        )

        for t in 线程对象列表:
            t.join()  # 等待全部完成
    """
    线程列表: List[threading.Thread] = []

    for 参数组 in 参数序列:
        if not isinstance(参数组, tuple):
            参数组 = (参数组,)
        线程 = threading.Thread(target=目标函数, args=参数组)
        线程.daemon = 守护线程
        线程.start()
        线程列表.append(线程)

    return 线程列表