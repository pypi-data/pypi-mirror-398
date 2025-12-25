import time
from datetime import datetime


def 倒计时(
        总秒数: int,
        前缀文本: str = "",
        显示时分秒: bool = False,
        显示系统时间: bool = False,
):
    """
    按秒打印倒计时，可选显示当前系统时间。

    功能说明：
        - 每秒打印剩余时间；
        - 可选择是否显示当前系统时间；
        - 剩余时间可打印为“时分秒”或纯秒数；
        - 输入非法不抛异常，直接结束。

    Args:
        总秒数 (int): 倒计时总秒数。
        前缀文本 (str): 打印提示文本，默认空。
        显示时分秒 (bool): 是否格式化为 时/分/秒 形式（默认 False）。
        显示系统时间 (bool): 是否打印当前系统时间（默认 False）。

    Returns:
        None
    """
    try:
        秒数 = int(总秒数)
        if 秒数 < 0:
            return

        while 秒数 > 0:
            # 剩余时间格式化
            if 显示时分秒:
                时 = 秒数 // 3600
                分 = (秒数 % 3600) // 60
                秒 = 秒数 % 60
                剩余 = f"{时}时 {分}分 {秒}秒"
            else:
                剩余 = f"{秒数} 秒"

            # 打印内容
            if 显示系统时间:
                当前时间 = datetime.now().strftime("%H:%M:%S")
                print(f"{前缀文本}当前时间：{当前时间} | 剩余：{剩余}")
            else:
                print(f"{前缀文本}{剩余}")

            time.sleep(1)
            秒数 -= 1

    except Exception:
        pass