def 分隔线(分隔符="=", 分割线长度=80):
    """
    打印一条分隔线。

    参数:
        - 分隔符 (str): 用于分隔线的字符。默认是 "="。
        - 分割线长度 (int): 分隔线的长度。默认是 80。
    """
    try:
        print(分隔符 * 分割线长度)
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False