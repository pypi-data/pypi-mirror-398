import shutil
import os


def 删除目录(目录路径):
    """
    删除指定的目录及其所有内容。

    参数：
        - 目录路径 (str)：要删除的目录路径。

    返回值：
        - bool：成功删除返回 True，失败返回 False。
    """
    try:
        if os.path.exists(目录路径):
            shutil.rmtree(目录路径)
            return True
        else:
            return False
    except Exception as e:
        return False