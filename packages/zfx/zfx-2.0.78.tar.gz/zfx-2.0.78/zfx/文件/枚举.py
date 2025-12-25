import os


def 枚举(目录路径):
    """
    枚举指定目录下的所有文件，并返回文件完整路径的列表。

    参数：
        - 目录路径：要枚举的目录路径。

    返回值：
        - 包含所有文件完整路径的列表（list）。
        - 如果发生异常或失败，则返回 False。

    异常：
        - 捕获所有异常，如果发生错误，返回 False。

    使用示例：
        目录路径 = r"C:\\Users\\example_directory"
        文件列表 = 枚举(目录路径)
        if 文件列表:
            print("找到以下文件：")
            for 文件 in 文件列表:
                print(文件)
        else:
            print("枚举失败或目录不存在。")
    """
    文件列表 = []
    try:
        # 使用 os.walk 遍历目录及其子目录
        for 根目录, 目录名, 文件名 in os.walk(目录路径):
            for 文件 in 文件名:
                文件完整路径 = os.path.join(根目录, 文件)
                文件列表.append(文件完整路径)
        return 文件列表  # 成功返回文件路径列表
    except Exception as e:
        print(f"枚举过程中发生错误：{e}")  # 输出错误信息
        return False  # 失败返回 False
