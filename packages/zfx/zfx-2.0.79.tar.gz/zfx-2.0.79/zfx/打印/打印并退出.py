import sys


def 打印并退出(
        *args,
        状态码: int = 0,
        颜色: str = "",
        启用颜色: bool = True,
) -> None:
    """
    打印内容后立即结束程序运行，可选彩色输出。
    常用于开发调试阶段：快速输出信息后终止程序。

    支持的颜色名称如下（不区分大小写）：

    【基础前景色】
        red            红色
        green          绿色
        yellow         黄色
        blue           蓝色
        magenta        洋红
        cyan           青色
        white          白色
        gray           灰色（深灰）

    【亮色系（Bright Colors）】
        bright_red        亮红
        bright_green      亮绿
        bright_yellow     亮黄
        bright_blue       亮蓝
        bright_magenta    亮洋红
        bright_cyan       亮青
        bright_white      亮白

    【背景色】
        bg_red            红色背景
        bg_green          绿色背景
        bg_yellow         黄色背景
        bg_blue           蓝色背景
        bg_magenta        紫色背景
        bg_cyan           青色背景
        bg_white          白色背景

    【文本样式】
        bold              加粗
        underline         下划线

    Args:
        *args: 需要打印的内容，与 print() 行为一致。
        状态码 (int): 程序退出码。0 表示正常退出，非 0 表示异常退出。
        颜色 (str): 彩色打印使用的颜色名称。空字符串表示不使用颜色。
        启用颜色 (bool): 是否启用彩色输出。False 时忽略颜色参数。

    Returns:
        None
    """
    try:
        文本 = " ".join(str(a) for a in args)

        if 启用颜色 and 颜色:
            色名 = str(颜色).lower()
            映射 = {
                # 基础色
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m",
                "gray": "\033[90m",

                # 亮色 Bright
                "bright_red": "\033[91m",
                "bright_green": "\033[92m",
                "bright_yellow": "\033[93m",
                "bright_blue": "\033[94m",
                "bright_magenta": "\033[95m",
                "bright_cyan": "\033[96m",
                "bright_white": "\033[97m",

                # 背景色
                "bg_red": "\033[41m",
                "bg_green": "\033[42m",
                "bg_yellow": "\033[43m",
                "bg_blue": "\033[44m",
                "bg_magenta": "\033[45m",
                "bg_cyan": "\033[46m",
                "bg_white": "\033[47m",

                # 文本样式
                "bold": "\033[1m",
                "underline": "\033[4m",
            }

            前缀 = 映射.get(色名)
            if 前缀:
                文本 = f"{前缀}{文本}\033[0m"

        print(文本)

    except Exception:
        pass

    finally:
        sys.exit(状态码)