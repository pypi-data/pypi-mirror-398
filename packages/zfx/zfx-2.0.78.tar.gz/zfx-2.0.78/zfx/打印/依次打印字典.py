def 依次打印字典(字典):
    """
    打印字典中的每个键值对。

    参数:
        - 字典 (dict): 要打印的字典。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。
    """
    try:
        for 键, 值 in 字典.items():
            print(f"{键}: {值}")
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False