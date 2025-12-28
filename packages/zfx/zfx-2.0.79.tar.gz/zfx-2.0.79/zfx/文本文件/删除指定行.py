def 删除指定行(文件路径, 行号):
    """
    删除指定文本文件中的某一行内容。文件编码格式必须为 UTF-8，否则可能导致读取或写入错误。

    参数:
        - 文件路径 (str): 要操作的文本文件路径，要求为 UTF-8 编码格式。
        - 行号 (int): 要删除的行号（从 1 开始计数）。

    返回值:
        - bool: 删除成功返回 True，删除失败返回 False。

    示例:
        删除成功 = 删除指定行('example.txt', 3)
        if 删除成功:
            print("指定行删除成功")
        else:
            print("指定行删除失败")

    注意:
        - 行号从 1 开始计数。如果行号无效（小于1或大于文件的总行数），则返回 False。
        - 此函数假设文本文件为 UTF-8 编码。如果文件是其他编码格式，可能会导致读取或写入失败。
    """
    try:
        # 以读写模式打开文件，使用 UTF-8 编码
        with open(文件路径, 'r+', encoding='utf-8') as file:
            行列表 = file.readlines()

            # 检查行号是否在有效范围内
            if 0 < 行号 <= len(行列表):
                行列表.pop(行号 - 1)  # 删除指定行

                # 写回剩余内容
                file.seek(0)
                file.writelines(行列表)
                file.truncate()  # 截断文件以移除多余内容
                return True

            return False
    except Exception:
        return False