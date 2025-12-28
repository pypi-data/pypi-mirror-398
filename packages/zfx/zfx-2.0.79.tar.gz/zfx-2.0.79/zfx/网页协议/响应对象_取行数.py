def 响应对象_取行数(响应对象):
    """
    功能：
        从服务器响应对象的文本中，统计总行数。
        行数按换行符进行分割，自动兼容 \n / \r\n / \r。

    参数：
        - 响应对象：
            requests.Response 类型对象，通常是 requests.get/post 的返回值。
            若传入 None，则直接返回 0。

    返回：
        - int：
            文本的总行数。
        - 0：
            当 响应对象 为 None 或出现异常时，返回 0。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 0。
        - 如果读取 .text 或分割时出错，返回 0。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/stream/3")
        >>> 行数 = 响应对象_取行数(r)
        >>> print(行数)
        3

        >>> 无效 = 响应对象_取行数(None)
        >>> print(无效)
        0

    注意事项：
        - 使用 .splitlines() 分割，能兼容不同平台的换行符。
        - 返回的是文本的逻辑行数，不包含换行符本身。
    """
    try:
        if 响应对象 is None:
            return 0
        文本内容 = 响应对象.text
        return len(文本内容.splitlines())
    except Exception:
        return 0
