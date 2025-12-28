import os


def 取目录大小(目录路径):
    """
    计算并返回指定目录的总大小（包括子目录中的所有文件）。

    参数：
        - 目录路径 (str)：要计算大小的目录路径。

    返回值：
        - int：目录的总大小（以字节为单位）。如果路径无效，则返回 0。
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(目录路径):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    except Exception:
        return 0

    return total_size
