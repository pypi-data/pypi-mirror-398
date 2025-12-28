import requests


def 测试Google可访问性(超时秒: float = 3.0) -> bool:
    """
    测试当前网络环境是否能正常访问 Google。

    功能说明:
        通过访问 Google 官方网站的 robots.txt 文件:
            https://www.google.com/robots.txt
        判断是否能够成功建立 HTTPS 连接并接收到响应。
        该文件体积极小、常年存在、缓存分布全球，是最稳定的检测入口。
        若请求成功且状态码为 200，则认为可访问 Google；
        否则判定为不可访问。

    Args:
        超时秒 (float, optional):
            请求超时时间（秒），默认 3 秒。

    Returns:
        bool:
            - True: 可以成功访问 Google。
            - False: 无法访问、超时或连接失败。
    """
    url = "https://www.google.com/robots.txt"
    try:
        响应对象 = requests.get(url, timeout=超时秒)
        return 响应对象.status_code == 200
    except Exception:
        return False
