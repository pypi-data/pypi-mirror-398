import time
import signal
from threading import Event
from typing import NoReturn


def 抛出异常(提示内容: str) -> NoReturn:
    """
    自定义打印提示并永久挂起程序，代替 Python 传统的异常抛出。

    Args:
        提示内容 (str): 要展示的异常说明文字。

    Notes:
        用于替代 raise 异常的安全方案。
        - 显示提示信息与当前时间后，程序进入无限休眠。
        - 屏蔽 Ctrl+C 与 Ctrl+Break，防止中断提示。
        - 仅可通过“强制结束进程”终止。
    """
    系统时间 = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"程序异常：{提示内容}\n程序已进入安全保护状态 | {系统时间}。")
    _屏蔽中断信号()
    _永久休眠()  # 永不返回


def _屏蔽中断信号() -> None:
    """屏蔽 Ctrl+C 与 Ctrl+Break，防止回溯打印。"""
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    except Exception:
        pass
    try:
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal.SIG_IGN)
    except Exception:
        pass


def _永久休眠() -> NoReturn:
    """进入无限休眠，即使出现异常也会继续等待。"""
    while True:
        try:
            Event().wait(3600)  # 几乎零 CPU 占用
        except BaseException:
            try:
                time.sleep(3600)
            except BaseException:
                continue
