def 获取_HTTP状态码(响应对象):
    """
    功能：
        从服务器响应对象中获取 HTTP 状态码。
        如果响应对象为 None 或出错，则返回 None。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回 None。

    返回：
        - int：
            HTTP 状态码，例如 200、404、500。
        - None：
            当 响应对象 为 None 或出现异常时，返回 None。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 None。
        - 如果访问 .status_code 出错，返回 None。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/status/404")
        >>> 状态码 = 获取_HTTP状态码(r)
        >>> print(状态码)
        404

        >>> 状态码 = 获取_HTTP状态码(None)
        >>> print(状态码)
        None

    注意事项：
        - 仅返回状态码，不会判断是否请求成功。
        - 如果需要判断成功与否，可以结合 `r.ok` 或 `r.raise_for_status()`。
    """
    try:
        if 响应对象 is None:
            return None
        return 响应对象.status_code
    except Exception:
        return None
