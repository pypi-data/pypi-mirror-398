import imaplib


def 连接服务器(服务器地址, 加密方式=True, 端口=None):
    """
    连接到IMAP服务器（支持加密和非加密连接）。

    参数:
        - 服务器地址 (str): IMAP服务器地址。
        - 加密方式 (bool): 是否使用加密连接（默认为True，表示使用SSL加密）。
        - 端口 (int, 可选): 自定义端口，若为None，则自动选择加密或非加密的标准端口。

    返回:
        - IMAP4_SSL 或 IMAP4 或 None: 成功返回连接对象，失败返回None。
    """
    try:
        if 加密方式:
            # 如果使用加密，默认端口为 993
            端口 = 端口 or 993
            邮箱 = imaplib.IMAP4_SSL(服务器地址, 端口)
        else:
            # 如果不使用加密，默认端口为 143
            端口 = 端口 or 143
            邮箱 = imaplib.IMAP4(服务器地址, 端口)
        return 邮箱
    except Exception:
        return None