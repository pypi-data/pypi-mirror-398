def 获取_响应URL(响应对象):
    """
    功能：
        从服务器响应对象中获取最终的 URL（response.url）。
        常用于检测重定向后的实际访问地址。
        如果响应对象为 None 或出错，则返回空字符串。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回 ""。

    返回：
        - str：
            最终的 URL 字符串。
        - ""：
            当 响应对象 为 None 或出现异常时，返回空字符串。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 ""。
        - 如果访问 .url 出错，也会返回 ""。

    示例：
        >>> import requests
        >>> r = requests.get("http://httpbin.org/redirect/1")
        >>> 最终地址 = 获取_响应URL(r)
        >>> print(最终地址)
        "http://httpbin.org/get"

        >>> 地址 = 获取_响应URL(None)
        >>> print(地址)
        ""

    注意事项：
        - .url 返回的是请求完成后的最终 URL，如果发生了重定向，会是跳转后的地址。
        - 如果你想获取历史跳转过程，可以查看 response.history。
    """
    try:
        if 响应对象 is None:
            return ''
        return 响应对象.url
    except Exception:
        return ''
