import os


def 取运行目录(是否添加尾斜杠=False):
    """
    获取当前程序的运行目录并返回绝对路径。可选择是否在路径尾部添加斜杠。

    参数：
        - 是否添加尾斜杠 (bool)：如果为 True，则在返回的目录路径尾部添加斜杠。默认为 False。

    返回值：
        - 运行目录路径：当前程序运行的目录绝对路径。如果无法获取，则返回 None。

    使用示例（可以复制并直接修改）：
        运行目录 = zfx_dir.取运行目录(是否添加尾斜杠=True)

        # 打印运行目录
        print("运行目录:", 运行目录)
    """
    try:
        # 获取当前工作目录
        运行目录 = os.getcwd()

        # 如果参数为 True，则在路径末尾添加斜杠
        if 是否添加尾斜杠:
            if not 运行目录.endswith(os.sep):  # os.sep 根据系统自动识别斜杠类型
                运行目录 += os.sep

        # 返回运行目录
        return 运行目录
    except Exception:
        return None