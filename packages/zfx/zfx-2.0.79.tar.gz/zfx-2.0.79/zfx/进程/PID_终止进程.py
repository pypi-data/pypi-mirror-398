import os
import signal


def PID_终止进程(pid, debug=True):
    """
    尝试通过指定的进程 PID 发送终止信号（SIGTERM）来关闭该进程。

    参数:
        - pid (int): 要终止的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - bool:
            - 终止成功返回 True；
            - 若进程不存在、无权限或发送失败，则返回 False。

    注意事项:
        1. 本函数使用 `os.kill(pid, signal.SIGTERM)`，终止信号为可被捕获的优雅退出（非强制杀死）。
        2. 如需强制杀死，可改为使用 `SIGKILL`（不推荐常用）。
        3. 在 Windows 下，signal.SIGTERM 实际被映射为 `TerminateProcess`，行为略有不同。
        4. 默认打印异常信息，若不希望打印可设置 debug=False。

    使用示例:
        状态 = PID_终止进程(1234)
        状态 = PID_终止进程(1234, debug=False)  # 静默模式
    """
    try:
        os.kill(int(pid), signal.SIGTERM)
        return True
    except Exception as e:
        if debug:
            print(f"[PID_终止进程] 终止失败：{e} (PID={pid})")
        return False
