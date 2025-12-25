import ctypes


def 清空回收站():
    """
    清空回收站中的所有文件和文件夹。

    返回:
        bool: 如果成功清空回收站返回 True，否则返回 False。

    示例:
        result = 系统_清空回收站()
    """
    try:
        # 定义回收站清空标志
        SHERB_NOCONFIRMATION = 0x00000001
        SHERB_NOPROGRESSUI = 0x00000004
        # 设置标志为直接清空
        flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI
        # 使用 SHEmptyRecycleBin 函数清空回收站
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        return True  # 成功清空回收站返回True
    except Exception:
        return False  # 出现异常或失败返回False
