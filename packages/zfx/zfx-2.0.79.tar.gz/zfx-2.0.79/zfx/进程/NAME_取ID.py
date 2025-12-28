import psutil


def NAME_取ID(进程名, debug=True):
    """
    根据进程名称获取首个匹配到的进程 ID。

    参数:
        - 进程名 (str): 要查找的进程名称（必须包含扩展名，例如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - int:
            - 找到时返回对应进程的 PID；
            - 未找到或出错时返回 0。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 如果系统中存在多个同名进程，仅返回第一个匹配的 PID。

    使用示例:
        pid = NAME_取ID("chrome.exe")
        pid = NAME_取ID("chrome.exe", debug=False)
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 进程名:
                return proc.info['pid']
        return 0
    except Exception as e:
        if debug:
            print(f"[NAME_取ID] 异常：{e} (进程名={进程名})")
        return 0
