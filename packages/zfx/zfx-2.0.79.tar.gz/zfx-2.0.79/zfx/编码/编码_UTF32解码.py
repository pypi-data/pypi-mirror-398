def 编码_UTF32解码(utf32_bytes):
    """
    将 UTF-32 编码的字节序列解码为字符串。

    参数:
        - utf32_bytes (bytes): UTF-32 编码的字节序列。

    返回:
        - 解码后的字符串 (str)。失败则返回 None
    """
    try:
        # 将 UTF-32 字节序列解码为字符串
        decoded_string = utf32_bytes.decode('utf-32')
        return decoded_string
    except Exception:
        return None