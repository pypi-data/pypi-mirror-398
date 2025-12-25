def 获取_响应cookies(响应对象):
    """
    功能：
        从服务器响应对象中获取 cookies。
        如果响应对象为 None 或出错，则返回空字典。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回空字典。

    返回：
        - dict：
            响应的 cookies 内容，以字典形式返回。
        - {}：
            当 响应对象 为 None 或出现异常时，返回空字典。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 {}。
        - 如果访问 .cookies 出错，也会返回 {}。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/cookies/set?name=value")
        >>> cookies = 获取_响应cookies(r)
        >>> print(cookies)
        {'name': 'value'}

        >>> cookies = 获取_响应cookies(None)
        >>> print(cookies)
        {}

    注意事项：
        - requests.Response.cookies 本身是一个 CookieJar 对象。
        - 通过 dict(响应对象.cookies) 可以将其转换为标准字典。
        - 如果需要在后续请求中使用 cookies，可以直接传给 requests 的 cookies 参数。
    """
    try:
        if 响应对象 is None:
            return {}
        # 转换为普通 dict，避免返回 CookieJar
        return dict(响应对象.cookies)
    except Exception:
        return {}
