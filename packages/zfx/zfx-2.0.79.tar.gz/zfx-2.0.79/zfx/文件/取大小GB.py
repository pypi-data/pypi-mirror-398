import os


def 取大小GB(文件完整路径):
    """
    获取指定文件的大小（以千兆字节为单位）。

    参数:
    文件完整路径 (str): 要获取大小的文件路径。

    返回:
    float: 文件的大小（千兆字节）,失败则返回None。
    """
    try:
        大小B = os.path.getsize(文件完整路径)
        return 大小B / (1024.0 * 1024.0 * 1024.0)
    except Exception:
        return None