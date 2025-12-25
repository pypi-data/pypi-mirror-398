import os


def 读运行目录文件(文件名称):
    """
    读取运行目录下的指定文本文件内容。文件应与运行的 Python 文件在同一目录，只需传递文本文件的名称，不需要传递完整路径。
    文件编码格式必须为 UTF-8，否则可能会导致读取错误。

    参数:
        - 文件名称 (str): 要读取的文本文件名称。

    返回值:
        - str: 成功时返回文件内容，失败时返回 None。

    示例:
        文件内容 = 读入运行目录下文件内容('example.txt')
        if 文件内容 is not None:
            print("文件内容读取成功:")
            print(文件内容)
        else:
            print("文件内容读取失败")

    注意:
        - 此函数假设文本文件是 UTF-8 编码。如果文件是其他编码格式，可能会导致读取失败。
    """
    try:
        # 获取运行目录下的完整文件路径
        文件路径 = os.path.join(os.getcwd(), 文件名称)

        # 以读取模式打开文件，使用 UTF-8 编码
        with open(文件路径, 'r', encoding='utf-8') as 文件:
            内容 = 文件.read()
        return 内容
    except Exception:
        return None