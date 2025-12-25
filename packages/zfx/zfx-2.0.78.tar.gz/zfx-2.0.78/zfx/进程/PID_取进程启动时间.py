import psutil
import datetime


def PID_取进程启动时间(pid, debug=True):
    """
    根据指定进程 PID 获取其启动时间，返回格式化后的时间字符串。

    参数:
        - pid (int): 要查询的进程 ID，例如 1234。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - str:
            - 成功时返回格式为 "YYYY-MM-DD HH:MM:SS" 的启动时间字符串；
            - 若失败，则返回空字符串。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 默认会输出异常信息，若不希望输出日志，可设置 debug=False。

    使用示例:
        启动时间 = PID_取进程启动时间(1234, debug=False)
    """
    try:
        pid = int(pid)
        try:
            process = psutil.Process(pid)
            start_time = process.create_time()
            return datetime.datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            if debug:
                print(f"[PID_取进程启动时间] 功能异常：{e} (PID={pid})")
            return ""
    except Exception as e:
        if debug:
            print(f"[PID_取进程启动时间] 参数或系统异常：{e} (PID={pid})")
        return ""
