import psutil


def NAME_是否为唯一实例(进程名, debug=True):
    """
    判断系统中是否仅存在一个指定名称的进程实例。

    参数:
        - 进程名 (str): 要判断的进程名称（必须包含扩展名，例如 python.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - bool:
            - 如果该进程仅存在一个实例，返回 True；
            - 多个实例或异常情况下返回 False。

    注意事项:
        1. 本函数依赖 `psutil` 库（已包含在本模块依赖中）。
        2. 区分大小写，建议传入完整名称。

    使用示例:
        唯一 = NAME_是否为唯一实例("python.exe")
        if 唯一:
            print("当前只有一个 python 实例运行中")
    """
    try:
        if not isinstance(进程名, str) or not 进程名:
            raise ValueError("参数必须为非空字符串")

        count = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 进程名:
                count += 1
                if count > 1:
                    return False
        return count == 1
    except Exception as e:
        if debug:
            print(f"[NAME_是否为唯一实例] 异常：{e} (进程名={进程名})")
        return False
