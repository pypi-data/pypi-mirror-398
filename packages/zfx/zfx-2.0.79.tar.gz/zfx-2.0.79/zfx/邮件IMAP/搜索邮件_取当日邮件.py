import datetime


def 搜索邮件_取当日邮件(连接对象):
    """
    获取当天的邮件。

    参数:
        - 连接对象 (IMAP4_SSL): IMAP4_SSL 连接对象。

    返回:
        - list: 包含符合当日日期的邮件的邮件ID列表。
    """
    try:
        # 获取当前日期
        today = datetime.date.today()

        # 格式化日期为 IMAP 标准格式: "DD-Mmm-YYYY"
        # 例如 "04-May-2024"
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        formatted_date = f"{today.day:02d}-{month_names[today.month - 1]}-{today.year}"

        # 构建IMAP搜索条件
        search_condition = f'ON "{formatted_date}"'

        # 使用 search 方法根据搜索条件查找邮件
        status, email_data = 连接对象.search(None, search_condition)

        # 如果搜索失败，返回空列表
        if status != "OK":
            return []

        # 返回符合条件的邮件ID列表
        email_id_list = email_data[0].split()
        return email_id_list

    except Exception:
        return []