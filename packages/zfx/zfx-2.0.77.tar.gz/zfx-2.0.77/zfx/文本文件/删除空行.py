def 删除空行(文件路径):
    """
    删除指定文本文件中的空行。文件编码格式必须为 UTF-8，否则可能导致读取或写入错误。

    参数:
        - 文件路径 (str): 要处理的文本文件路径，要求为 UTF-8 编码格式。

    返回值:
        - bool: 删除成功返回 True，删除失败返回 False。

    示例:
        删除成功 = 删除空行('example.txt')
        if 删除成功:
            print("空行删除成功")
        else:
            print("空行删除失败")

    注意:
        - 此函数假设文本文件为 UTF-8 编码。如果文件是其他编码格式，可能会导致读取或写入失败。
    """
    try:
        # 打开文件读取所有行
        with open(文件路径, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 过滤掉空行
        non_empty_lines = [line for line in lines if line.strip()]

        # 将非空行写回文件
        with open(文件路径, 'w', encoding='utf-8') as file:
            file.writelines(non_empty_lines)

        return True
    except Exception:
        return False