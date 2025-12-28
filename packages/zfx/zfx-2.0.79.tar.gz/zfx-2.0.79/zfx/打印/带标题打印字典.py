def 带标题打印字典(字典, 标题):
    """
    打印带标题的字典。

    参数:
        - 字典 (dict): 要打印的字典。
        - 标题 (str): 字典的标题。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。
    """
    try:
        print(标题)
        print("=" * len(标题))
        for 键, 值 in 字典.items():
            print(f"{键}: {值}")
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False