import psutil


def 进程_枚举():
    """
    枚举系统中所有运行的进程，返回进程名称和进程ID的字典。

    返回值:
        - dict: 键为进程名称，值为进程ID列表的字典。

    使用示例:
    进程字典 = 进程_枚举()
    """
    try:
        processes = {}
        # 遍历所有运行中的进程
        for proc in psutil.process_iter(['pid', 'name']):
            name = proc.info['name']
            pid = proc.info['pid']
            if name in processes:
                processes[name].append(pid)
            else:
                processes[name] = [pid]
        return processes  # 返回包含所有进程名称和进程ID的字典
    except Exception:
        return {}  # 捕获所有异常并返回空字典