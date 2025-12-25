def 搜索邮件_按发件人(连接对象, 发件人):
    """
    根据发件人搜索邮件。

    参数:
        - 连接对象 (IMAP4_SSL 或 IMAP4): 已建立的 IMAP 连接对象。支持加密（SSL）和非加密（普通）协议。
        - 发件人 (str): 要搜索的发件人邮箱。

    返回:
        - list: 包含符合条件的邮件ID列表。如果没有符合条件的邮件，返回空列表。

    示例:
        邮件ID列表 = 搜索邮件_按发件人(连接对象, "someone@example.com")
    """
    try:
        搜索条件 = f'FROM "{发件人}"'
        状态, 邮件数据 = 连接对象.search(None, 搜索条件)
        if 状态 != "OK":
            return []
        邮件ID列表 = 邮件数据[0].split()
        return 邮件ID列表
    except Exception:
        return []