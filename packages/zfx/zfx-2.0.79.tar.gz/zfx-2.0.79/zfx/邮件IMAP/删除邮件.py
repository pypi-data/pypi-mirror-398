def 删除邮件(连接对象, 邮件ID列表):
    """
    删除指定邮件ID的邮件。

    参数:
        - 连接对象 (IMAP4_SSL 或 IMAP4): 已建立的 IMAP 连接对象。支持加密（SSL）和非加密（普通）协议。
        - 邮件ID列表 (list): 要删除的邮件ID列表。

    返回:
        - bool: 删除成功返回 True，失败返回 False。

    示例:
        删除邮件(连接对象, [b'1', b'3', b'5'])
    """
    try:
        # 标记邮件为删除
        for 邮件ID in 邮件ID列表:
            连接对象.store(邮件ID, '+FLAGS', '\\Deleted')

        # 执行 expunge 删除标记为删除的邮件
        连接对象.expunge()

        return True
    except Exception:
        return False