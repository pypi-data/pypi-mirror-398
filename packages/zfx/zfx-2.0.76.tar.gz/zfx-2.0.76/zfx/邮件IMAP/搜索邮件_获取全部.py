def 搜索邮件_获取全部(连接对象):
    """
    获取当前已选择文件夹中所有邮件的ID列表。

    参数:
        - 连接对象: 使用 连接函数 返回的连接对象（IMAP4_SSL 或 IMAP4）。

    返回:
        - list: 返回所有邮件的ID列表。
    """
    try:
        # 使用 search 方法根据 "ALL" 条件查找所有邮件
        status, email_ids = 连接对象.search(None, "ALL")
        if status == "OK":
            return email_ids[0].split()  # 返回邮件ID列表
        else:
            return []
    except Exception:
        return []