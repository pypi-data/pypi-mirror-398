import psutil


def 进程_取进程列表():
    """
    获取系统中所有正在运行的进程名称。

    返回值:
        - list: 包含所有正在运行的进程名称的列表。

    使用示例:
    进程列表 = 进程_取进程列表()
    """
    try:
        process_names = [proc.info['name'] for proc in psutil.process_iter(['name'])]
        return process_names
    except Exception:
        return []
