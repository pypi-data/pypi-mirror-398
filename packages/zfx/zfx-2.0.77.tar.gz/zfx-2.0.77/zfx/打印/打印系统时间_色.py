from datetime import datetime
from typing import Optional


def 打印系统时间_色(
    前缀: str = "",
    格式: Optional[str] = "%Y-%m-%d %H:%M:%S",
    颜色: str = "cyan",
) -> bool:
    """
    打印当前系统时间（彩色版本），支持自定义前缀、格式与颜色。

    功能说明：
        - 获取当前系统时间，并根据用户指定格式进行格式化；
        - 支持彩色输出，通过 ANSI 颜色码增强可读性；
        - 若格式字符串非法，将自动降级为默认格式 "%Y-%m-%d %H:%M:%S"；
        - 颜色名称不区分大小写，若未匹配到，将自动使用无色打印；
        - 本函数不抛异常，是底层打印工具函数的安全实现。

    Args:
        前缀 (str): 打印在时间前的文本内容，可为空。
        格式 (str | None): 时间格式化字符串，遵循 datetime.strftime 规则。
                           若格式无效，将使用默认格式。
        颜色 (str): 输出颜色名称，支持以下值：
            - 基础色：red, green, yellow, blue, magenta, cyan, white, gray
            - 亮色：bright_red, bright_green, bright_yellow, bright_blue,
                    bright_magenta, bright_cyan, bright_white
            - 背景：bg_red, bg_green, bg_yellow, bg_blue, bg_magenta, bg_cyan, bg_white
            - 样式：bold, underline
            - plain（无颜色）

    Returns:
        bool:
            True：打印成功；
            False：出现异常。

    Notes:
        - 若终端不支持 ANSI 颜色，将以普通文本显示；
        - 前缀不为空时，会在前缀与时间文本之间自动加一个空格；
        - 颜色选择不匹配时自动降级为 plain（无色）。
    """
    try:
        # 内部颜色映射（独立，不依赖外部模块）
        颜色映射 = {
            # 基础色
            "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
            "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
            "white": "\033[37m", "gray": "\033[90m",

            # 亮色
            "bright_red": "\033[91m", "bright_green": "\033[92m",
            "bright_yellow": "\033[93m", "bright_blue": "\033[94m",
            "bright_magenta": "\033[95m", "bright_cyan": "\033[96m",
            "bright_white": "\033[97m",

            # 背景色
            "bg_red": "\033[41m", "bg_green": "\033[42m", "bg_yellow": "\033[43m",
            "bg_blue": "\033[44m", "bg_magenta": "\033[45m", "bg_cyan": "\033[46m",
            "bg_white": "\033[47m",

            # 文本样式
            "bold": "\033[1m", "underline": "\033[4m",

            "plain": "",
        }

        # 获取颜色前缀
        色 = 颜色映射.get(颜色.lower(), "")

        # 获取当前时间
        时间对象 = datetime.now()

        # 格式处理，非法自动降级
        try:
            时间文本 = 时间对象.strftime(格式) if 格式 else 时间对象.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            时间文本 = 时间对象.strftime("%Y-%m-%d %H:%M:%S")

        # 组合最终输出文本
        文本 = f"{前缀} {时间文本}" if 前缀 else 时间文本

        # 打印彩色文本
        if 色:
            print(f"{色}{文本}\033[0m")
        else:
            print(文本)

        return True

    except Exception:
        return False