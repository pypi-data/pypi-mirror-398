def 带标题打印列表(列表, 标题):
    """
    打印带标题的列表。

    参数:
        - 列表 (list): 要打印的列表。
        - 标题 (str): 列表的标题。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。
    """
    try:
        print(标题)
        print("=" * len(标题))
        for 元素 in 列表:
            print(元素)
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False