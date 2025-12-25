import os


def 强制重启():
    """
    强制重启计算机。

    使用命令 "shutdown /r /f /t 0" 来实现强制重启。

    示例:
        系统_强制重启()
    """
    os.system("shutdown /r /f /t 0")
