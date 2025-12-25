import base64


def 编码_BASE64解码(编码数据):
    """
    对输入的 BASE64 编码数据进行解码。

    参数：
    编码数据: 待解码的 BASE64 编码数据。
    编码数据长度必须是4的倍数

    返回值：
    解码后的原始数据，如果解码失败则返回假。
    """
    try:
        # 将 BASE64 编码数据转换为字节串
        编码的字节串 = 编码数据.encode('utf-8')

        # 进行 BASE64 解码
        解码的字节串 = base64.b64decode(编码的字节串)

        # 将字节串解码为字符串并返回
        return 解码的字节串.decode('utf-8')
    except Exception:
        return False