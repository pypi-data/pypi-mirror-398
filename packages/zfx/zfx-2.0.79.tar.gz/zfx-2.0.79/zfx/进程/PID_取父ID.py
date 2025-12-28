import psutil


def PID_取父ID(pid, debug=True):
    """
    根据进程 ID 获取其父进程的 ID。

    参数:
        - pid (int): 要查询的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - int:
            - 成功时返回父进程的 ID；
            - 如果进程不存在、访问失败或参数异常，返回 0。

    注意事项:
        1. 若目标进程不存在，或无权限访问其信息，会返回 0。
        2. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。

    使用示例:
        父ID = PID_取父ID(1234)
        父ID = PID_取父ID("4567", debug=False)
    """
    try:
        pid = int(pid)
        try:
            return psutil.Process(pid).ppid()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            if debug:
                print(f"[PID_取父ID] 功能异常：{e} (PID={pid})")
            return 0
    except Exception as e:
        if debug:
            print(f"[PID_取父ID] 参数或系统异常：{e} (PID={pid})")
        return 0
