# 安全打印.py
import threading
from typing import Any

_打印锁 = threading.Lock()


def 安全打印(*args: Any, **kwargs: Any) -> None:
    """
    在线程环境中安全打印，避免多线程输出交叉。

    功能说明：
        使用全局锁包裹 print，确保同一时刻只有一个线程在输出。
        适合调试、进度日志等需要可读性的场景。

    Args:
        *args: 传递给内置 print 的位置参数。
        **kwargs: 传递给内置 print 的关键字参数（如 end、sep、flush）。

    Returns:
        None
    """
    with _打印锁:
        print(*args, **kwargs)