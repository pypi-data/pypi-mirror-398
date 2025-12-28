import requests


def 获取外网IP():
    """
    获取当前外网IP。

    :return: 成功返回IP地址字符串，失败返回None。
    """
    try:
        响应 = requests.get('http://myip.ipip.net/')
        if 响应.status_code == 200:
            return 响应.text.strip()  # 去除响应内容前后的空白字符
        else:
            return None
    except Exception:
        return None