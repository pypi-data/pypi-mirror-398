def 获取_响应编码(响应对象):
    """
    功能：
        从服务器响应对象中获取编码格式（encoding）。
        如果响应对象为 None 或出错，则返回空字符串。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回 ""。

    返回：
        - str：
            响应的编码格式，例如 "utf-8"、"ISO-8859-1"。
        - ""：
            当 响应对象 为 None 或出现异常时，返回空字符串。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 ""。
        - 如果访问 .encoding 出错，也会返回 ""。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/html")
        >>> 编码 = 获取_响应编码(r)
        >>> print(编码)
        "utf-8"

        >>> 编码 = 获取_响应编码(None)
        >>> print(编码)
        ""

    注意事项：
        - requests 会自动根据 HTTP 头或页面内容推测编码。
        - 如果需要更准确的编码，可以结合 `r.apparent_encoding`。
        - 修改 `r.encoding` 会影响 `r.text` 的解码方式。
    """
    try:
        if 响应对象 is None:
            return ''
        return 响应对象.encoding or ''
    except Exception:
        return ''
