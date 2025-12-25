def 断开连接(服务器对象):
    """
    断开与邮件服务器的连接。

    参数:
        - 服务器对象 (poplib.POP3): 已连接的POP3服务器对象。

    返回值:
        - bool: 如果断开成功，则返回True；否则返回False。
    """
    try:
        服务器对象.quit()
        return True
    except Exception:
        return False