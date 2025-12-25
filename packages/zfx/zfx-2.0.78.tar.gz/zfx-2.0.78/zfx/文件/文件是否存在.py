import os


def 文件是否存在(文件完整路径):
    """
    检查文件是否存在，并捕获可能的异常。

    参数：
        - 文件完整路径：要检查的文件路径。

    返回值：
        - 如果文件存在，返回 True；否则返回 False。

    异常：
        - 如果在检查文件过程中发生错误（如权限问题），则捕获异常并返回 False。

    使用示例：
        文件路径 = "/path/to/file.txt"
        是否存在 = 文件是否存在(文件路径)
        if 是否存在:
            print("文件存在")
        else:
            print("文件不存在")
    """
    try:
        return os.path.exists(文件完整路径)
    except Exception:
        return False