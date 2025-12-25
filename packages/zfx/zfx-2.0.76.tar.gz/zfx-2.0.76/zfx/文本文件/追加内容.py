def 追加内容(文件路径, 内容):
    """
    向指定的文本文件末尾追加内容。文件编码格式必须为 UTF-8，否则可能会导致写入错误。

    参数:
        - 文件路径 (str): 要追加内容的文本文件路径，要求为 UTF-8 编码格式。
        - 内容 (str): 要追加的内容。

    返回值:
        - bool: 如果追加成功，返回 True；否则返回 False。

    示例:
        追加成功 = 追加内容('example.txt', '追加的内容\n')
        if 追加成功:
            print("内容追加成功")
        else:
            print("内容追加失败")

    注意:
        - 此函数假设文本文件是 UTF-8 编码。如果文件是其他编码格式，可能会导致写入失败。
    """
    try:
        # 以追加模式打开文件，使用 UTF-8 编码
        with open(文件路径, 'a', encoding='utf-8') as 文件:
            文件.write(内容)
        return True
    except Exception:
        return False