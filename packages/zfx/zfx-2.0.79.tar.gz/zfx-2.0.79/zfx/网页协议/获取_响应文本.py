def 获取_响应文本(响应对象):
    """
    功能：
        从服务器响应对象中获取文本内容（response.text）。
        如果响应对象为 None 或出错，则返回空字符串。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回 ""。

    返回：
        - str：
            响应的文本内容（通常是 HTML、JSON 字符串等）。
        - ""：
            当 响应对象 为 None 或出现异常时，返回空字符串。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 ""。
        - 如果访问 .text 出错（例如响应对象不合法），也会返回 ""。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/get")
        >>> 文本 = 获取_响应文本(r)
        >>> print(文本[:60])
        "{\\n  \\"args\\": {}, \\n  \\"headers\\": {..."

        >>> 文本 = 获取_响应文本(None)
        >>> print(文本)
        ""

    注意事项：
        - 返回内容的解码方式由 `响应对象.encoding` 决定。
        - 如果编码推断不准确，可以先手动设置 `响应对象.encoding` 后再调用本函数。
    """
    try:
        if 响应对象 is None:
            return ''
        return 响应对象.text
    except Exception:
        return ''
