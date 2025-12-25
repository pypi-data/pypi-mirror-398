def 彩色打印(
        文本: str,
        级别: str = "info",
        启用颜色: bool = True,
) -> None:
    """
    按不同级别以彩色打印文本（扩展多种颜色）。

    支持级别（不区分大小写）：
        info        → 青色
        success     → 绿色
        warning     → 黄色
        error       → 红色
        debug       → 紫色
        plain       → 无色

        blue        → 蓝色
        cyan        → 青色（同 info）
        magenta     → 洋红
        gray        → 灰色
        white       → 白色
        bold        → 加粗无色文本
        underline   → 下划线

        bright_red      → 亮红色
        bright_green    → 亮绿色
        bright_yellow   → 亮黄色
        bright_blue     → 亮蓝色
        bright_magenta  → 亮紫色
        bright_cyan     → 亮青色
        bright_white    → 亮白色

        bg_red          → 红色背景
        bg_green        → 绿色背景
        bg_yellow       → 黄色背景
        bg_blue         → 蓝色背景
        bg_magenta      → 紫色背景
        bg_cyan         → 青色背景
        bg_white        → 白色背景

    Args:
        文本 (str): 要打印的内容。
        级别 (str): 颜色名称。
        启用颜色 (bool): 是否启用彩色打印，默认 True。

    Returns:
        None
    """
    try:
        # foreground & background ANSI codes
        色 = str(级别).strip().lower()

        颜色映射 = {
            # 基础
            "info": "\033[36m",
            "success": "\033[32m",
            "warning": "\033[33m",
            "error": "\033[31m",
            "debug": "\033[35m",
            "plain": "",

            # 扩展文本色
            "blue": "\033[34m",
            "cyan": "\033[36m",
            "magenta": "\033[35m",
            "gray": "\033[90m",
            "white": "\033[37m",

            # 文本样式
            "bold": "\033[1m",
            "underline": "\033[4m",

            # 亮色（Bright）
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
        }

        if not 启用颜色:
            print(文本)
            return

        前缀 = 颜色映射.get(色, 颜色映射["info"])
        重置 = "\033[0m"

        if 前缀:
            print(f"{前缀}{文本}{重置}")
        else:
            print(文本)

    except Exception:
        pass