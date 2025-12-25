import requests


def 取IP信息_ipinfo() -> dict | None:
    """
    获取当前出口公网 IP 及地理位置信息（通过 ipinfo.io 接口）。

    功能说明:
        访问 ipinfo.io 提供的全球公共接口:
            https://ipinfo.io/json

        返回的数据为 JSON 格式，包含以下典型字段:
            - ip: 出口公网 IP 地址。
            - hostname: 对应主机名（若可解析）。
            - city: 城市名称。
            - region: 省份或地区名称。
            - country: 国家代码（如 CN、US、JP）。
            - loc: 经纬度（格式: "纬度,经度"）。
            - org: 所属组织或 ISP（网络运营商名称）。
            - postal: 邮政编码（若有）。
            - timezone: 时区（如 "Asia/Shanghai"）。

        该接口由 ipinfo.io 官方提供，无需认证，全球可访问。
        若请求失败或响应异常，函数返回 None。

    Returns:
        dict | None:
            - 成功时返回包含出口 IP 与地理信息的字典。
            - 失败时返回 None。
    """
    url = "https://ipinfo.io/json"
    try:
        响应对象 = requests.get(url, timeout=5)
        if 响应对象.status_code == 200:
            return 响应对象.json()
        return None
    except Exception:
        return None