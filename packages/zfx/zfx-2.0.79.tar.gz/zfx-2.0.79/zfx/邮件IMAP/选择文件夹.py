def 选择文件夹(连接对象, 文件夹名称, readonly=False):
    """
    选择指定的邮箱文件夹，默认允许修改邮件。

    参数:
        - 连接对象: 使用 连接函数 返回的连接对象（IMAP4_SSL 或 IMAP4）。
        - 文件夹名称 (str): 要选择的文件夹名称（例如 "INBOX"）。
        - readonly (bool): 是否只读。默认为 False，表示可以修改邮件；True 表示只能读取。

    返回:
        - bool: 选择成功返回 True，失败返回 False。

    小提示：
        - 常用的IMAP邮箱文件夹名称包括：
        - 收件箱： "INBOX"
        - 草稿箱： "Drafts"
        - 已发送： "Sent"
        - 垃圾邮件： "Junk"
        - 垃圾箱： "Trash"
        - 存档： "Archive"
        - 不同的邮件服务提供商可能使用不同的文件夹名称，但这些是较为常见的标准文件夹。您也可以根据需要检查服务器上实际存在的文件夹名称
    """
    try:
        # 使用 select 方法选择文件夹，readonly决定是否可以修改文件夹中的邮件
        status, messages = 连接对象.select(文件夹名称, readonly=readonly)
        if status == "OK":
            return True
        else:
            return False
    except Exception:
        return False