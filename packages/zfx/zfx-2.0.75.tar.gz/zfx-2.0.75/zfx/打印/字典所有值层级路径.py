def 字典所有值层级路径(字典, 当前路径=""):
    """
    递归打印字典中所有值的层级路径。

    参数:
        - 字典 (dict): 要打印的字典。
        - 当前路径 (str, optional): 当前的层级路径，默认是空字符串。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。
    """
    try:
        for 键, 值 in 字典.items():
            新路径 = f"{当前路径}/{键}" if 当前路径 else 键
            if isinstance(值, dict):
                字典所有值层级路径(值, 新路径)
            elif isinstance(值, list):
                for 索引, 项 in enumerate(值):
                    if isinstance(项, dict):
                        字典所有值层级路径(项, f"{新路径}[{索引}]")
                    else:
                        print(f"{新路径}[{索引}] = {项}")
            else:
                print(f"{新路径} = {值}")
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False