import ctypes


def 是否为管理员():
    """
    检查当前程序是否以管理员权限运行。

    返回:
        bool: 如果是管理员返回 True，否则返回 False。

    示例:
        is_admin = 系统_是否为管理员()
    """
    try:
        # 使用Windows API来检查当前进程是否以管理员权限运行
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False