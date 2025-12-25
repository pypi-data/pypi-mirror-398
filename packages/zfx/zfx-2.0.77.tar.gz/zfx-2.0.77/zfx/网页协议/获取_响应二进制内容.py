def 获取_响应二进制内容(响应对象):
    """
    功能：
        从服务器响应对象中获取二进制内容（response.content）。
        常用于下载文件、图片、音频、视频等非文本数据。
        如果响应对象为 None 或出错，则返回空字节串。

    参数：
        - 响应对象 (requests.Response)：
            requests.get / post 返回的 Response 对象。
            如果传入 None，则直接返回 b""。

    返回：
        - bytes：
            响应的二进制内容。
        - b""：
            当 响应对象 为 None 或出现异常时，返回空字节串。

    异常处理逻辑：
        - 如果 响应对象 为 None，立即返回 b""。
        - 如果访问 .content 出错，也会返回 b""。

    示例：
        >>> import requests
        >>> r = requests.get("https://httpbin.org/image/png")
        >>> 数据 = 获取_响应二进制内容(r)
        >>> print(len(数据) > 0)
        True

        >>> 数据 = 获取_响应二进制内容(None)
        >>> print(数据)
        b""

    注意事项：
        - 与 .text 不同，.content 返回的是原始字节流，不会尝试解码。
        - 适合用于保存文件：例如 with open(..., "wb") 写入。
        - 如果需要分块下载大文件，建议使用 `iter_content()` 而不是直接读取 .content。
    """
    try:
        if 响应对象 is None:
            return b''
        return 响应对象.content
    except Exception:
        return b''
