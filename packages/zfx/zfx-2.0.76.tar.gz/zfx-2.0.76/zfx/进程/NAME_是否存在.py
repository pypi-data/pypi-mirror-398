import psutil


def NAME_是否存在(进程名, debug=True):
    """
    判断系统中是否存在指定名称的进程。

    参数:
        - 进程名 (str): 要查询的进程名称（如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - bool:
            - 存在则返回 True；
            - 不存在或查询异常则返回 False。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 进程名称区分大小写，建议输入完整名称。

    使用示例:
        是否有浏览器 = NAME_是否存在("chrome.exe")
        if 是否有浏览器:
            print("浏览器正在运行")
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")

        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 进程名:
                return True
        return False
    except Exception as e:
        if debug:
            print(f"[NAME_是否存在] 异常：{e} (进程名={进程名})")
        return False
