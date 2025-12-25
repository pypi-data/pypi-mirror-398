import base64


def 编码_BASE64编码(数据):
    """
    对输入的数据进行 BASE64 编码。

    参数：
    data: 待编码的数据，可以是字符串或字节串。

    返回值：
    编码后的 BASE64 字符串，如果编码失败或者出现异常则返回False。
    """
    try:
        # 如果输入的是字符串，将其转换为字节串
        if isinstance(数据, str):
            数据 = 数据.encode('utf-8')

        # 进行 BASE64 编码
        编码后的数据 = base64.b64encode(数据)

        # 将字节串解码为字符串并返回
        return 编码后的数据.decode('utf-8')
    except Exception:
        return False