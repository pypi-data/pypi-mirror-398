import random


def 取随机范围数字(起始数, 结束数):
    """
    生成一个介于 a 到 b 之间的随机整数，包括两个端点。

    参数:
        - 起始数 (int): 随机数生成范围的下限。
        - 结束数 (int): 随机数生成范围的上限。

    返回:
        - int: 随机生成的整数，范围在 起始数 到 结束数 之间，并包含 起始数 和 结束数。如果发生异常，返回 None。

    使用示例:
        随机数 = zfx_textutils.取随机范围数字(1, 100)
        print(随机数)  # 输出一个 1 到 100 之间的随机整数
    """
    try:
        return random.randint(起始数, 结束数)
    except Exception:
        return None