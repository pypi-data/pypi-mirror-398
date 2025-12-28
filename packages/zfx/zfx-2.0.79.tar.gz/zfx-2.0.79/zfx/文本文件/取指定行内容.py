def 取指定行内容(文件路径, 行号):
    """
    获取指定文本文件中特定行的内容。文件编码格式必须为 UTF-8，否则可能导致读取错误。

    参数:
        - 文件路径 (str): 要读取的文本文件路径，要求为 UTF-8 编码格式。
        - 行号 (int): 要获取内容的行号（从 1 开始计数）。

    返回值:
        - str: 成功时返回指定行的内容。失败或行号无效时返回 None。

    示例:
        行内容 = 取指定行内容('示例.txt', 3)
        if 行内容 is not None:
            print("行内容:", 行内容)
        else:
            print("获取行内容失败")

    注意:
        - 行号从 1 开始计数。如果行号小于 1 或超出文件行数范围，将返回 None。
        - 此函数假设文本文件为 UTF-8 编码。如果文件是其他编码格式，可能会导致读取失败。
    """
    try:
        # 以读取模式打开文件，使用 UTF-8 编码
        with open(文件路径, 'r', encoding='utf-8') as file:
            行内容 = file.readlines()

        # 检查行号是否有效
        if 行号 < 1 or 行号 > len(行内容):
            return None

        # 返回指定行的内容，去除行尾的换行符
        return 行内容[行号 - 1].rstrip('\n')
    except Exception:
        return None