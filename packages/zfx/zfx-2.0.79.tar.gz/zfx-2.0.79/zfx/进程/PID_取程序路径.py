import psutil


def PID_取程序路径(pid, debug=True):
    """
    根据指定进程 PID 获取其可执行文件的完整路径。

    参数:
        - pid (int): 要查询的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - str:
            - 成功时返回程序完整路径；
            - 若进程不存在、访问失败或参数异常，则返回空字符串。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 路径通常是如 `C:\\Program Files\\xxx\\xxx.exe` 的绝对路径。

    使用示例:
        路径 = PID_取程序路径(1234)
        路径 = PID_取程序路径("5678", debug=False)
    """
    try:
        pid = int(pid)
        try:
            return psutil.Process(pid).exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            if debug:
                print(f"[PID_取程序路径] 功能异常：{e} (PID={pid})")
            return ""
    except Exception as e:
        if debug:
            print(f"[PID_取程序路径] 参数或系统异常：{e} (PID={pid})")
        return ""
