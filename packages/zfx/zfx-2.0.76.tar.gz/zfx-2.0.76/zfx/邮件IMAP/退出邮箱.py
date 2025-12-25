def 退出邮箱(连接对象):
    """
    使用IMAP连接对象退出邮箱并关闭连接。

    参数:
        - 连接对象: 使用 连接函数 返回的连接对象（IMAP4_SSL 或 IMAP4）。

    返回:
        - bool: 退出成功返回 True，失败返回 False。
    """
    try:
        连接对象.logout()  # 使用 IMAP 连接对象执行退出操作
        return True
    except Exception:
        return False