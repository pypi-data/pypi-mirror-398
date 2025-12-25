def 编码_UTF8解码(字节串):
    """
    将 UTF-8 编码的字节序列解码为 Unicode 字符串。

    参数：
        - 字节串（bytes）：要解码的 UTF-8 编码的字节序列。

    返回：
        - str 或 bool：如果成功解码，则返回表示解码后的 Unicode 字符串，否则返回 False。

    使用示例
    字节串 = b'\xe7\xac\x91\xe7\xac\x91'
    print(编码_UTF8解码(字节串))
    """
    try:
        解码后字符串 = 字节串.decode('utf-8')
        return 解码后字符串
    except Exception:
        return False