def 指定行插入内容(文件路径, 行号, 内容):
    """
    在指定行前插入内容。文件编码格式必须为 UTF-8，否则可能导致读取或写入错误。

    参数:
        - 文件路径 (str): 要操作的文本文件路径，要求为 UTF-8 编码格式。
        - 行号 (int): 插入内容的位置（行号），从 1 开始计数。
        - 内容 (str): 要插入的内容。

    返回值:
        - bool: 如果插入成功，返回 True；否则返回 False。

    示例:
        插入成功 = 指定行插入内容('example.txt', 3, '这是插入的内容')
        if 插入成功:
            print("内容插入成功")
        else:
            print("内容插入失败")

    注意:
        - 行号从 1 开始计数。如果行号大于文件行数，则会插入到文件末尾。
        - 此函数假设文本文件为 UTF-8 编码。如果文件是其他编码格式，可能会导致读取或写入失败。
    """
    try:
        # 以读写模式打开文件，使用 UTF-8 编码
        with open(文件路径, 'r+', encoding='utf-8') as file:
            行列表 = file.readlines()

            # 插入内容到指定行，行号从 1 开始
            行列表.insert(行号 - 1, 内容 + '\n')

            # 重置文件指针到文件开头，并写回修改后的内容
            file.seek(0)
            file.writelines(行列表)

        return True
    except Exception:
        return False