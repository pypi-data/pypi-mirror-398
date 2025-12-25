def 目录树(目录, 层级=0):
    """
    打印带有层级结构的目录树。

    参数:
        - 目录 (dict or list): 目录结构的数据，字典或列表形式。
        - 层级 (int, optional): 当前层级的缩进。默认是 0。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。
    """
    try:
        if isinstance(目录, dict):
            for 键, 值 in 目录.items():
                print("    " * 层级 + str(键))
                if isinstance(值, (dict, list)):
                    目录树(值, 层级 + 1)
                else:
                    print("    " * (层级 + 1) + str(值))
        elif isinstance(目录, list):
            for 项 in 目录:
                if isinstance(项, (dict, list)):
                    目录树(项, 层级 + 1)
                else:
                    print("    " * 层级 + str(项))
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False