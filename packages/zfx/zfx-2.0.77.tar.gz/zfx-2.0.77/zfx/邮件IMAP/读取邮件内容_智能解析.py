import email
from email.header import decode_header


def 读取邮件内容_智能解析(连接对象, 邮件ID):
    """
    通过邮件ID智能解析邮件内容。如果智能解析失败则请使用：读取邮件内容_原始内容 功能获取邮件原始内容自行解析

    参数:
        - 连接对象 (imaplib.IMAP4_SSL or imaplib.IMAP4): 已连接的IMAP服务器对象。
        - 邮件ID (str): 要读取的邮件ID。

    返回:
        - dict: 包含邮件内容的字典，格式如下:
            {
                "发件人": str,
                "收件人": str,
                "主题": str,
                "正文": str (文本格式优先，其次HTML),
                "HTML": str (如果有HTML内容)
            }
        - 若读取失败，则返回 None。
    """
    try:
        # 获取邮件的原始数据
        状态, 数据 = 连接对象.fetch(邮件ID, "(RFC822)")
        if 状态 != "OK":
            return None

        # 解析邮件内容
        原始邮件 = 数据[0][1]
        邮件对象 = email.message_from_bytes(原始邮件)

        # 解析发件人
        发件人 = 邮件对象["From"]
        if 发件人:
            发件人 = decode_header(发件人)[0][0]
            if isinstance(发件人, bytes):
                发件人 = 发件人.decode()

        # 解析收件人
        收件人 = 邮件对象["To"]

        # 解析主题
        主题, 编码 = decode_header(邮件对象["Subject"])[0]
        if isinstance(主题, bytes):
            主题 = 主题.decode(编码 or "utf-8")

        # 解析邮件正文
        正文 = None
        HTML = None
        if 邮件对象.is_multipart():
            for part in 邮件对象.walk():
                内容类型 = part.get_content_type()
                if 内容类型 == "text/plain":
                    正文 = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                elif 内容类型 == "text/html":
                    HTML = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
        else:
            正文 = 邮件对象.get_payload(decode=True).decode(邮件对象.get_content_charset() or "utf-8", errors="ignore")

        return {
            "发件人": 发件人,
            "收件人": 收件人,
            "主题": 主题,
            "正文": 正文 or HTML,  # 优先返回文本格式
            "HTML": HTML,
        }

    except Exception:
        return None