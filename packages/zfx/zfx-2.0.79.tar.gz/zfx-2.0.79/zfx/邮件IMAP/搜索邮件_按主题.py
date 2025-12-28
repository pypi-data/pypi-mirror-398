def 搜索邮件_按主题(连接对象, 主题):
    """
    根据主题搜索邮件。

    参数:
        - 连接对象 (IMAP4_SSL 或 IMAP4): 已建立的 IMAP 连接对象。支持加密（SSL）和非加密（普通）协议。
        - 主题 (str): 要搜索的邮件主题。

    返回:
        - list: 包含符合条件的邮件ID列表。如果没有符合条件的邮件，返回空列表。

    示例:
        邮件ID列表 = 搜索邮件_按主题(连接对象, "Meeting")
    """
    try:
        搜索条件 = f'SUBJECT "{主题}"'
        状态, 邮件数据 = 连接对象.search(None, 搜索条件)
        if 状态 != "OK":
            return []
        邮件ID列表 = 邮件数据[0].split()
        return 邮件ID列表
    except Exception:
        return []