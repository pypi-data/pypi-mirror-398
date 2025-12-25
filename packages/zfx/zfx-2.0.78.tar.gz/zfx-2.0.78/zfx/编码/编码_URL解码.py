import urllib.parse


def 编码_URL解码(字符串):
    """
    对字符串进行 URL 解码。

    参数:
        - 字符串 (str): 要进行解码的字符串。

    返回:
        - 解码后的字符串 (str)。发生异常则返回None
    """
    try:
        解码后的字符串 = urllib.parse.unquote(字符串)
        return 解码后的字符串
    except Exception:
        return None