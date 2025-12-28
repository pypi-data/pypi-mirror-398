import psutil
import datetime


def NAME_获取首个运行时间(进程名, debug=True):
    """
    获取指定名称的所有进程中最早启动的时间（即首个运行时间）。

    参数:
        - 进程名 (str): 要查询的进程名称（必须包含扩展名，例如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - str:
            - 成功时返回最早启动时间，格式为 "YYYY-MM-DD HH:MM:SS"；
            - 若未找到或发生异常则返回空字符串。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 某些系统进程可能因权限问题而被跳过。
        3. 时间为本地时间，受操作系统时区影响。

    使用示例:
        首启时间 = NAME_获取首个运行时间("chrome.exe")
        print("最早运行时间:", 首启时间)
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")

        启动时间戳列表 = []
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 进程名:
                try:
                    启动时间戳列表.append(proc.create_time())
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        if 启动时间戳列表:
            最早启动 = min(启动时间戳列表)
            return datetime.datetime.fromtimestamp(最早启动).strftime("%Y-%m-%d %H:%M:%S")
        return ""
    except Exception as e:
        if debug:
            print(f"[NAME_获取首个运行时间] 异常：{e} (进程名={进程名})")
