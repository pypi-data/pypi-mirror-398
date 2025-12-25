import psutil


def PID_取线程数(pid, debug=True):
    """
    根据指定进程 PID 获取其当前线程数。

    参数:
        - pid (int): 要查询的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - int:
            - 成功时返回线程数量；
            - 若进程不存在、访问失败或参数异常，则返回 0。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 线程数包括主线程和所有由该进程启动的子线程。

    使用示例:
        线程数 = PID_取线程数(1234)
        线程数 = PID_取线程数("9876", debug=False)
    """
    try:
        pid = int(pid)
        try:
            return psutil.Process(pid).num_threads()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            if debug:
                print(f"[PID_取线程数] 功能异常：{e} (PID={pid})")
            return 0
    except Exception as e:
        if debug:
            print(f"[PID_取线程数] 参数或系统异常：{e} (PID={pid})")
        return 0
