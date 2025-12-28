def 搜索邮件_自定义条件(连接对象, 搜索条件="ALL"):
    """
    在 IMAP 邮箱中根据指定条件搜索邮件。

    参数:
        - 连接对象 (IMAP4_SSL): 已建立的 IMAP 连接对象（使用 `连接服务器` 返回的对象）。
        - 搜索条件 (str): IMAP 搜索命令的标准字符串形式。默认为 "ALL"，表示搜索所有邮件。可以使用其他条件进行过滤，如：
            - "FROM"：按发件人搜索，例如 'FROM "someone@example.com"'。
            - "TO"：按收件人搜索，例如 'TO "someone@example.com"'。
            - "SUBJECT"：按主题搜索，例如 'SUBJECT "Important Email"'。
            - "SINCE"：按日期搜索，例如 'SINCE "1-Jan-2024"'。
            - "BEFORE"：按日期搜索，例如 'BEFORE "31-Dec-2024"'。
            - "UNSEEN"：搜索未读邮件。
            - "FLAGGED"：搜索已标记的邮件。
            - "DELETED"：搜索已删除邮件等。
            - 组合条件：例如，`'(UNSEEN) (FROM "someone@example.com")'` 或 `'(SINCE "1-Jan-2024") (SUBJECT "Meeting")'`。

    返回:
        - list: 包含符合搜索条件的邮件的邮件ID列表。如果没有符合条件的邮件，返回空列表。

    示例:
        - # 使用默认搜索条件，获取所有邮件
          邮件ID列表 = 搜索邮件_自定义条件(连接对象)

        - # 搜索发件人为 "someone@example.com" 的邮件
          邮件ID列表 = 搜索邮件_自定义条件(连接对象, 'FROM "someone@example.com"')

        - # 搜索主题包含 "important" 的未读邮件
          邮件ID列表 = 搜索邮件_自定义条件(连接对象, '(UNSEEN) (SUBJECT "important")')

        - # 搜索2024年1月1日之后的邮件
          邮件ID列表 = 搜索邮件_自定义条件(连接对象, 'SINCE "1-Jan-2024"')

        - # 组合条件：获取2024年1月1日之后且主题包含 "meeting" 的未读邮件
          搜索条件 = '(SINCE "1-Jan-2024") (SUBJECT "meeting") (UNSEEN)'
          邮件ID列表 = 搜索邮件_自定义条件(连接对象, 搜索条件)

    注意:
        - 搜索条件必须符合 IMAP 标准的字符串格式。例如 `FROM "someone@example.com"` 或 `(SUBJECT "test")`。
        - 可以使用逻辑运算符组合多个条件，如使用括号 `()` 将条件分组。
    """
    try:
        状态, 邮件数据 = 连接对象.search(None, 搜索条件)
        if 状态 != "OK":
            return []
        邮件ID列表 = 邮件数据[0].split()
        return 邮件ID列表
    except Exception:
        return []