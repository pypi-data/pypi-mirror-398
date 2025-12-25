def 登录邮箱(连接对象, 用户名, 密码):
    """
    使用IMAP连接对象进行邮箱登录。

    参数:
        - 连接对象: 使用 连接函数 返回的连接对象（IMAP4_SSL 或 IMAP4）。
        - 用户名 (str): 邮箱账户名。
        - 密码 (str): 邮箱密码。

    返回:
        - bool: 登录成功返回 True，失败返回 False。
    """
    try:
        连接对象.login(用户名, 密码)  # 使用 IMAP 连接对象进行登录
        return True
    except Exception:
        return False