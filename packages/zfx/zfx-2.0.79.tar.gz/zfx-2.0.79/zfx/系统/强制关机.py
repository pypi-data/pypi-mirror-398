import os


def 强制关机():
    # 在 Windows 上使用命令 "shutdown /s /f /t 0" 来强制关机
    os.system("shutdown /s /f /t 0")
