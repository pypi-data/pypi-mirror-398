def 获取文件夹列表(连接对象):
    """
    获取邮箱中的所有文件夹列表。

    参数:
        - 连接对象: 使用 连接函数 返回的连接对象（IMAP4_SSL 或 IMAP4）。

    返回:
        - list: 包含邮箱中所有文件夹名称的列表，如果获取失败返回空列表。
    """
    try:
        # 获取邮箱中的所有文件夹
        文件夹列表 = []
        status, data = 连接对象.list()
        if status == "OK":
            # data 是一个列表，每个元素表示一个文件夹信息
            for folder_info in data:
                folder_name = folder_info.decode().split(' "/" ')[-1]  # 解析文件夹名称
                文件夹列表.append(folder_name)
        return 文件夹列表
    except Exception:
        return []