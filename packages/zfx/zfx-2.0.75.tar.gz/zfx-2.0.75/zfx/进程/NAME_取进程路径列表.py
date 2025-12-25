import psutil


def NAME_取进程路径列表(进程名, debug=True):
    """
    获取系统中所有指定名称进程的可执行文件路径列表。

    参数:
        - 进程名 (str): 要查询的进程名称（必须包含扩展名，例如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - list[str]:
            - 成功时返回进程路径列表；
            - 若未找到或发生异常则返回空列表。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 进程路径通常是如 `C:\\Program Files\\xxx\\xxx.exe` 的绝对路径。
        3. 某些系统进程可能无权访问路径，将自动跳过。

    使用示例:
        路径列表 = NAME_取进程路径列表("python.exe")
        for 路径 in 路径列表:
            print("程序路径:", 路径)
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")

        路径列表 = []
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 进程名:
                try:
                    路径列表.append(proc.exe())
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    continue  # 忽略无法访问的进程
        return 路径列表
    except Exception as e:
        if debug:
            print(f"[NAME_取进程路径列表] 异常：{e} (进程名={进程名})")
        return []
