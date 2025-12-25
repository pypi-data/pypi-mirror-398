import os


def 创建目录(目录路径, 是否递归=False):
    """
    创建指定路径的目录。如果目录已存在，则不会重新创建。

    参数：
        - 目录路径 (str)：要创建的目录的路径。
        - 是否递归 (bool)：如果为 True，则创建多级目录（即递归创建父目录）。默认为 False。

    返回值：
        - bool：返回 True 表示目录成功创建或已存在，返回 False 表示创建失败。

    使用示例（可以复制并直接修改）：
        执行结果 = zfx_dir.创建目录("E:/my_project/新目录", 是否递归=True)

        if 执行结果:
            print("目录创建成功或已存在。")
        else:
            print("目录创建失败。")
    """
    try:
        if 是否递归:
            # 递归创建目录，包括父目录
            os.makedirs(目录路径, exist_ok=True)
        else:
            # 创建单层目录，如果已存在则不会报错
            os.mkdir(目录路径)

        return True
    except Exception:
        return False