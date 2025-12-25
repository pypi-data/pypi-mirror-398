import requests


def 取Cloudflare节点访问信息() -> str | None:
    """
    获取 Cloudflare 边缘节点返回的访问信息原文。

    功能说明:
        访问 Cloudflare 官方公共接口 `https://www.cloudflare.com/cdn-cgi/trace`，
        并返回其原始响应内容（纯文本形式）。
        该接口包含客户端 IP、访问节点地区、时间戳、TLS 协议版本等信息。
        本函数不进行任何解析或格式化，仅返回完整原文字符串。

    Returns:
        str | None:
            - 成功时返回接口原文字符串。
            - 请求失败或发生异常时返回 None。
    """
    url = "https://www.cloudflare.com/cdn-cgi/trace"
    try:
        响应对象 = requests.get(url, timeout=5)
        if 响应对象.status_code == 200:
            return 响应对象.text
        return None
    except Exception:
        return None