from typing import List, Optional
import threading

def 等待线程结束_批量(线程列表: List[threading.Thread], 超时时间: Optional[float] = None) -> None:
    """
    批量等待多个线程执行完毕。

    功能说明：
        用于一次性等待多个线程完成，可配合“启动线程_批量()”使用。
        函数会依次 join 每个线程，确保所有线程都结束后再继续执行。

    Args:
        线程列表 (List[threading.Thread]):
            要等待的线程对象列表。

        超时时间 (float, 可选):
            每个线程的最大等待秒数，默认 None 表示一直等待。

    Returns:
        None

    注意事项：
        - 若某线程在超时前未结束，不会强制终止，仅跳过等待。
        - 若所有线程都是守护线程，则无需调用此函数，因为守护线程会随主程序退出。
        - 若要统计执行进度，可在循环中加入打印逻辑。

    用法示例（非交互）：
        线程们 = 启动线程_批量(任务函数, 参数列表)
        等待线程结束_批量(线程们)
    """
    for 线程 in 线程列表:
        if isinstance(线程, threading.Thread):
            线程.join(timeout=超时时间)