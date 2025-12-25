import psutil


def NAME_统计数量(进程名, debug=True):
    """
    统计系统中与指定进程名称匹配的实例数量。

    参数:
        - 进程名 (str): 要查询的进程名称（必须包含扩展名，例如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - int:
            - 成功时返回进程实例数量；
            - 出错或无匹配进程时返回 0。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 进程名称区分大小写，建议输入完整的文件名。

    使用示例:
        数量 = NAME_统计数量("python.exe")
        if 数量 > 1:
            print("检测到多个 python 实例")
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")

        count = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 进程名:
                count += 1
        return count
    except Exception as e:
        if debug:
            print(f"[NAME_统计数量] 异常：{e} (进程名={进程名})")
        return 0
