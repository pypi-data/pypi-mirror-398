import hashlib


def 编码_SHA1哈希(字符串):
    """
    对字符串进行 SHA-1 哈希。

    参数:
        - 字符串 (str): 要进行哈希的字符串。

    返回:
        - 哈希值 (str)。失败则返回 None
    """
    try:
        哈希对象 = hashlib.sha1(字符串.encode('utf-8'))
        哈希值 = 哈希对象.hexdigest()
        return 哈希值
    except Exception:
        return None