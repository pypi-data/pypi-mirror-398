def 带索引打印列表(列表):
    """
    打印列表中的每个元素及其索引。

    参数:
        - 列表 (list): 要打印的列表。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。
    """
    try:
        for 索引, 元素 in enumerate(列表):
            print(f"{索引}: {元素}")
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False