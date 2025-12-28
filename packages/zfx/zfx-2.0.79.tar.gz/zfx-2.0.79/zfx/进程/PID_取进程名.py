import psutil


def PID_取进程名(pid, debug=True):
    """
    根据进程 ID 获取其进程名。

    参数:
        - pid (int): 要查询的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - str:
            - 成功时返回进程名字符串，例如 "chrome.exe"；
            - 如果进程不存在、访问失败或参数异常，返回空字符串 ""。

    注意事项:
        1. 若目标进程不存在，或无权限访问其信息，会返回 ""。
        2. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。

    使用示例:
        进程名 = PID_取进程名(1234)
        进程名 = PID_取进程名("4567", debug=False)
    """
    try:
        pid = int(pid)
        try:
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            if debug:
                print(f"[PID_取进程名] 功能异常：{e} (PID={pid})")
            return ""
    except Exception as e:
        if debug:
            print(f"[PID_取进程名] 参数或系统异常：{e} (PID={pid})")
        return ""
