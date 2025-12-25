def 获取_响应头(响应对象):
    """
    功能：
        从服务器响应对象中获取响应头（headers），并返回字典形式。
        如果响应对象为 None 或出错，则返回空字典。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回 {}。

    返回：
        - dict：
            响应头的字典形式，例如 {"Content-Type": "text/html; charset=utf-8"}。
        - {}：
            当 响应对象 为 None 或出现异常时，返回空字典。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 {}。
        - 如果访问 .headers 出错，也会返回 {}。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/get")
        >>> headers = 获取_响应头(r)
        >>> print(headers.get("Content-Type"))
        "application/json"

        >>> headers = 获取_响应头(None)
        >>> print(headers)
        {}

    注意事项：
        - 返回结果本质上是一个 CaseInsensitiveDict，可以像普通字典一样使用。
        - 如果需要转换为真正的 dict，可以调用 dict()。
    """
    try:
        if 响应对象 is None:
            return {}
        return dict(响应对象.headers)
    except Exception:
        return {}
