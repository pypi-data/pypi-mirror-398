import zlib


def 编码_CRC32(字符串):
    """
    计算字符串的 CRC32 校验和。

    参数:
        - 字符串 (str): 要计算校验和的字符串。

    返回:
        - CRC32 校验和 (int)。
    """
    try:
        return zlib.crc32(字符串.encode('utf-8'))
    except Exception:
        return None