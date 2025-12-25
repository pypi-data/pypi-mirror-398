import os


def 取大小B(文件完整路径):
    """
    获取指定文件的大小（以字节为单位）。

    参数:
    文件完整路径 (str): 要获取大小的文件路径。

    返回:
    int: 文件的大小（字节）,失败则返回None
    """
    try:
        return os.path.getsize(文件完整路径)
    except Exception:
        return None