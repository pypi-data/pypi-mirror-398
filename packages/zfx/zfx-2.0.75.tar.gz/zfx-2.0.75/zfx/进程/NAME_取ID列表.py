import psutil


def NAME_取ID列表(进程名, debug=True):
    """
    根据进程名称获取所有匹配的进程 PID 列表。

    参数:
        - 进程名 (str): 要查找的进程名称（必须包含扩展名，例如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - list[int]:
            - 成功时返回所有匹配进程的 PID 列表；
            - 未找到或出错时返回空列表。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 匹配方式为完全相等（区分大小写，推荐传入完整名称）。

    使用示例:
        id列表 = NAME_取ID列表("chrome.exe")
        id列表 = NAME_取ID列表("chrome.exe", debug=False)
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")

        pid_list = []
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 进程名:
                pid_list.append(proc.info['pid'])
        return pid_list
    except Exception as e:
        if debug:
            print(f"[NAME_取ID列表] 异常：{e} (进程名={进程名})")
        return []
