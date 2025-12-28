import socket


def 网络是否通畅(测试地址: str = "8.8.8.8", 端口: int = 53, 超时秒: float = 3.0) -> bool:
    """
    检查当前网络是否通畅（通过尝试连接公共 DNS 服务器）。

    功能说明:
        尝试建立到指定 IP 地址与端口的 TCP 连接，以判断网络连通性。
        默认使用 Google 公共 DNS (8.8.8.8:53)。
        若连接成功，视为网络正常；若超时或异常，则判定为网络不通。

        可用于快速检测:
            - 当前机器是否能访问互联网。
            - 网络是否被防火墙阻断。
            - 出口是否可达全球公共节点。

    Args:
        测试地址 (str, optional):
            要测试的目标 IP 地址。
            常用:
                - 8.8.8.8  (Google DNS，全球通用)
                - 114.114.114.114 (中国大陆 DNS)
            默认为 "8.8.8.8"。
        端口 (int, optional):
            目标端口号，DNS 服务使用 53。
        超时秒 (float, optional):
            连接超时时间（秒）。

    Returns:
        bool:
            - True: 网络通畅。
            - False: 网络不通或超时。
    """
    try:
        with socket.create_connection((测试地址, 端口), timeout=超时秒):
            return True
    except Exception:
        return False
