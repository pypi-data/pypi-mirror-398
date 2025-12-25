import html


def 编码_HTML解码(字符串):
    """
    对 HTML 字符串进行解码。

    参数:
        - 字符串 (str): 要进行解码的 HTML 字符串。

    返回:
        - 解码后的字符串 (str)。失败则返回 None
    """
    try:
        解码后的字符串 = html.unescape(字符串)
        return 解码后的字符串
    except Exception:
        return None