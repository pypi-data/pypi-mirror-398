def 修改指定行内容(文件路径, 行号, 新内容):
    """
    修改指定文本文件中的某一行内容。文件格式必须为 UTF-8 编码，否则可能导致读取或写入时出错。

    参数：
        - 文件路径：要修改的文本文件路径，要求为 UTF-8 编码格式。
        - 行号：要修改的行号（从 1 开始计数）。
        - 新内容：要替换该行的新内容。

    返回值：
        - bool：如果修改成功返回 True，失败返回 False。

    使用示例：
        修改结果 = 修改指定行内容('文件路径.txt', 3, '这是新的内容')

        # 替换第 3 行的内容为 '这是新的内容'。

    注意：
        - 此函数假设文本文件是 UTF-8 编码。如果文件是其他编码格式（如 GBK 等），则可能导致读取或写入失败。
    """
    try:
        # 打开文件并读取所有行，假定文件为 UTF-8 编码
        with open(文件路径, 'r', encoding='utf-8') as file:
            行列表 = file.readlines()

        # 检查行号是否在范围内
        if 行号 < 1 or 行号 > len(行列表):
            return False

        # 替换指定行的内容
        行列表[行号 - 1] = 新内容 + '\n'

        # 写回修改后的内容，保持 UTF-8 编码
        with open(文件路径, 'w', encoding='utf-8') as file:
            file.writelines(行列表)

        return True
    except Exception:
        return False