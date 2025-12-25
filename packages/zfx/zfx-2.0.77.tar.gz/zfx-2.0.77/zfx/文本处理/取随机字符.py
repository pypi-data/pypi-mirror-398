import random
import string


def 取随机字符(要取的字符数, 获取模式=1):
    """
    返回随机生成的指定数量和模式的字符。

    参数：
        - 要取的字符数 (int): 指定要生成的字符数量。
        - 获取模式 (int): 指定要生成的字符模式。1=数字, 2=小写字母, 4=大写字母, 8=特殊字符。
                          可以组合多个模式，例如：获取模式=2 | 4 会同时包含小写字母和大写字母。

    返回值：
        - str: 随机生成的字符字符串。如果发生异常，返回空字符串。

    示例：
        随机数字 = zfx_textutils.取随机字符(10, 1)
        print("随机数字:", 随机数字)

        随机字母 = zfx_textutils.取随机字符(10, 2 | 4)
        print("随机字母:", 随机字母)

        随机字符 = zfx_textutils.取随机字符(10, 1 | 2 | 4 | 8)
        print("随机字符:", 随机字符)
    """
    try:
        # 初始化可见字符集合
        可见字符集合 = ""

        # 根据获取模式决定字符集合
        if 获取模式 & 1:
            可见字符集合 += string.digits  # 数字
        if 获取模式 & 2:
            可见字符集合 += string.ascii_lowercase  # 小写字母
        if 获取模式 & 4:
            可见字符集合 += string.ascii_uppercase  # 大写字母
        if 获取模式 & 8:
            可见字符集合 += string.punctuation  # 特殊字符

        # 如果未设置有效的获取模式，抛出异常
        if not 可见字符集合:
            raise ValueError("无效的获取模式")

        # 从可见字符集合中随机选择指定数量的字符
        随机字符列表 = random.choices(可见字符集合, k=要取的字符数)

        # 返回生成的随机字符
        return ''.join(随机字符列表)
    except Exception:
        return ""  # 发生异常时返回空字符串