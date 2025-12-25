import threading
from typing import Optional


def 等待线程结束(线程对象: threading.Thread, 超时时间: Optional[float] = None) -> None:
    """
    等待指定线程执行完毕。

    功能说明：
        主程序会在这里暂停，直到目标线程执行完成或达到超时时间。
        若线程是守护线程，主程序一般不需要等待；若是关键任务线程，则建议使用此函数。

    Args:
        线程对象 (threading.Thread):
            要等待的线程对象。

        超时时间 (float, 可选):
            最长等待秒数，默认 None 表示一直等到线程结束。
            若线程在超时前未结束，函数会直接返回，线程仍在后台运行。

    Returns:
        None

    注意事项：
        - 该函数只等待，不会强制终止线程。
        - 若线程执行中出现异常，异常会在线程内部输出，不会影响此函数。
        - 若想轮询多个线程，请使用 `等待线程结束_批量()`。

    用法示例（非交互）：
        t = 启动线程(任务函数, "下载A")
        等待线程结束(t)  # 等待任务完成
    """
    if isinstance(线程对象, threading.Thread):
        线程对象.join(timeout=超时时间)