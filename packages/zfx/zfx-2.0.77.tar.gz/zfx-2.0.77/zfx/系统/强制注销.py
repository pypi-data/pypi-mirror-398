import os


def 强制注销():
    """
    强制注销当前用户。

    使用命令 "shutdown /l /f" 来实现强制注销。

    示例:
        系统_强制注销()
    """
    os.system("shutdown /l /f")
