import requests


def 取公网IP_Amazon() -> str | None:
    """
    获取当前出口公网 IP 地址（通过 Amazon 公共接口）。

    功能说明:
        访问 Amazon 官方提供的全球公共接口:
            https://checkip.amazonaws.com/
        返回结果为纯文本格式，仅包含当前访问者的出口公网 IP。
        无需认证，全球范围可用，响应速度快、稳定性高。
        适用于网络诊断、代理检测、出口地址识别等场景。

    Returns:
        str | None:
            - 成功时返回出口公网 IP 地址字符串，例如 "203.0.113.15"。
            - 请求失败或发生异常时返回 None。
    """
    url = "https://checkip.amazonaws.com/"
    try:
        响应对象 = requests.get(url, timeout=5)
        if 响应对象.status_code == 200:
            return 响应对象.text.strip()
        return None
    except Exception:
        return None