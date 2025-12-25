def 搜索邮件_按收件人(连接对象, 收件人邮箱):
    """
    通过收件人邮箱搜索邮件。

    参数:
        - 连接对象 (imaplib.IMAP4_SSL or imaplib.IMAP4): 已连接的IMAP服务器对象。
        - 收件人邮箱 (str): 要搜索的收件人邮箱地址。

    返回:
        - list: 匹配的邮件ID列表，若无匹配邮件则返回空列表。

    说明:
        使用 IMAP 搜索语法中的 `TO` 关键字来根据收件人邮箱搜索邮件。
        IMAP 的 `TO` 关键字用于匹配邮件的收件人字段。如果没有使用正确的搜索关键字，
        可能会导致搜索失败或者返回不正确的结果。
    """
    try:
        # 选择邮件文件夹（默认选择收件箱）
        连接对象.select("inbox")

        # 使用IMAP的搜索条件，按收件人邮箱来搜索邮件
        状态, 数据 = 连接对象.search(None, f'TO "{收件人邮箱}"')

        if 状态 == "OK":
            邮件ID列表 = 数据[0].split()
            return 邮件ID列表
        else:
            return []

    except Exception:
        return []