def 读取邮件内容_原始内容(连接对象, 邮件ID):
    """
    通过邮件ID获取邮件的原始内容。

    参数:
        - 连接对象 (imaplib.IMAP4_SSL or imaplib.IMAP4): 已连接的IMAP服务器对象。
        - 邮件ID (str): 要读取的邮件ID。

    返回:
        - bytes: 邮件的原始数据（RFC822格式），可以自行解析。
        - 若读取失败，则返回 None。
    """
    try:
        # 获取邮件的原始数据
        状态, 数据 = 连接对象.fetch(邮件ID, "(RFC822)")
        if 状态 != "OK":
            return None

        # 原始邮件数据
        原始邮件 = 数据[0][1]
        return 原始邮件

    except Exception:
        return None