def 读入全部内容(文件路径):
    """
    读取指定文件路径的文本文件内容。文件编码格式必须为 UTF-8，否则可能会导致读取错误。

    参数:
        - 文件路径 (str): 要读取的文本文件的路径，要求为 UTF-8 编码格式。

    返回值:
        - str: 成功时返回文件内容，失败时返回 None。

    示例:
        文件内容 = 读入全部内容('示例.txt')
        if 文件内容 is not None:
            print("文件内容:", 文件内容)
        else:
            print("读取文件失败")

    注意:
        - 此函数假设文本文件为 UTF-8 编码。如果文件是其他编码格式，可能会导致读取失败。
    """
    try:
        # 以读取模式打开文件，使用 UTF-8 编码
        with open(文件路径, 'r', encoding='utf-8') as file:
            文件内容 = file.read()
        return 文件内容
    except Exception:
        return None