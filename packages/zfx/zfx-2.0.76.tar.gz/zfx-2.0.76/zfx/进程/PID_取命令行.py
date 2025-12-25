import psutil


def PID_取命令行(pid, debug=True):
    """
    根据指定进程 PID 获取其启动时的命令行参数列表。

    参数:
        - pid (int): 要查询的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - list[str]:
            - 成功时返回命令行参数列表（包含可执行文件及所有启动参数）。
            - 若进程不存在、访问失败或参数异常，则返回空列表。

    注意事项:
        1. 命令行参数可能包含程序路径、参数开关等内容，具体取决于目标进程。
        2. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。

    使用示例:
        参数列表 = PID_取命令行(1234)
        参数列表 = PID_取命令行("1234", debug=False)
    """
    try:
        pid = int(pid)
        try:
            return psutil.Process(pid).cmdline()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            if debug:
                print(f"[PID_取命令行] 功能异常：{e} (PID={pid})")
            return []
    except Exception as e:
        if debug:
            print(f"[PID_取命令行] 参数或系统异常：{e} (PID={pid})")
        return []
