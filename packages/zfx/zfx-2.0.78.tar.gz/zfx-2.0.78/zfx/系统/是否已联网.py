import socket


def 是否已联网():
    """
    检查当前系统是否已经联网。

    返回:
        bool: 如果已联网返回 True，否则返回 False。

    示例:
        result = 系统_是否已联网()
    """
    try:
        # 使用 socket 创建一个 TCP 套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置超时时间为 3 秒
        s.settimeout(3)
        # 尝试连接到一个已知的互联网域名
        s.connect(("myip.ipip.net", 80))
        # 连接成功，表示已联网
        return True
    except Exception:
        # 连接失败，表示未联网
        return False