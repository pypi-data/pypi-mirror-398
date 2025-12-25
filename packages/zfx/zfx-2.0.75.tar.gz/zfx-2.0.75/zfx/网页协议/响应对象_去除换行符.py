def 响应对象_去除换行符(响应对象):
    """
    功能：
        从服务器响应对象中获取文本内容，并移除其中的所有换行符
        （包括 '\n' 和 '\r'），返回一行连续的字符串。

    参数：
        - 响应对象：
            requests.Response 类型对象，通常是 requests.get/post 的返回值。
            若传入 None，则直接返回空字符串。

    返回：
        - str：
            处理后的字符串，原始响应文本中所有换行符均已去除。
        - str（空字符串）：
            当 响应对象 为 None 或出现异常时，返回 ""。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回空字符串。
        - 如果读取 .text 或替换时出错，也会返回空字符串。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/get")
        >>> 内容 = 响应对象_去除换行符(r)
        >>> print(内容[:80])
        '{"args": {}, "headers": {"Accept": "*/*", "Host": "httpbin.org", ...'

    注意事项：
        - 本函数仅去除换行符，不会去除空格或制表符。
        - 如果需要更复杂的清理（如去掉多余空格、HTML 标签），应在此基础上再做处理。
    """
    try:
        if 响应对象 is None:
            return ''
        文本内容 = 响应对象.text
        return 文本内容.replace('\n', '').replace('\r', '')
    except Exception:
        return ''
