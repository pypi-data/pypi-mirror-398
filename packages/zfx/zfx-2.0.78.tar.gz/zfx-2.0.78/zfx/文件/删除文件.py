import os


def 删除文件(文件完整路径):
    """
    删除指定的文件，并捕获可能的异常。

    参数:
    文件完整路径 (str): 要删除的文件路径。

    返回:
    bool: 如果文件成功删除返回True，否则返回False。
    """
    try:
        if os.path.exists(文件完整路径):
            os.remove(文件完整路径)
            return True
        else:
            return False
    except Exception:
        return False