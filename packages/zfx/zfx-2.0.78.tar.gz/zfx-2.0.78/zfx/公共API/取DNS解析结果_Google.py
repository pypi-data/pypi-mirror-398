import requests


def 取DNS解析结果_Google(域名: str) -> dict | None:
    """
    使用 Google 公共 DNS over HTTPS 接口解析指定域名。

    功能说明:
        访问 Google 提供的全局 DNS 解析接口：
        https://dns.google/resolve?name=<域名>
        返回解析结果的完整 JSON 数据。
        该接口可用于获取 A、AAAA、CNAME、MX 等记录。
        若请求失败或返回无效，函数返回 None。

    Args:
        域名 (str):
            需要解析的目标域名，例如 "example.com" 或 "www.google.com"。

    Returns:
        dict | None:
            - 成功时返回包含 DNS 解析结果的 JSON 字典。
            - 请求失败或解析异常时返回 None。
    """
    try:
        url = f"https://dns.google/resolve?name={域名}"
        响应对象 = requests.get(url, timeout=5)
        if 响应对象.status_code == 200:
            return 响应对象.json()
        return None
    except Exception:
        return None
