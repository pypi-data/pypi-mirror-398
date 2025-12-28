def 打印变量信息(
        变量名称: str,
        变量值,
        *,
        最大展示长度: int = 500,
        启用颜色: bool = True,
        颜色_名称: str = "cyan",
) -> None:
    """
    打印变量的名称、类型与值，用于调试时快速查看变量的状态。

    功能说明：
        - 输出变量名称、变量类型、变量内容；
        - 内容过长时自动截断，避免输出过多信息；
        - 支持彩色输出（内部独立实现 ANSI 颜色码，不依赖其他函数）；
        - 整个过程不抛出异常，适合作为底层调试工具。

    支持颜色：
        基础前景色：
            red, green, yellow, blue, magenta, cyan, white, gray
        亮色系：
            bright_red, bright_green, bright_yellow, bright_blue,
            bright_magenta, bright_cyan, bright_white
        背景色：
            bg_red, bg_green, bg_yellow, bg_blue, bg_magenta, bg_cyan, bg_white
        文本样式：
            bold, underline
        plain（无颜色）

    Args:
        变量名称 (str): 变量的名称，作为打印时的提示。
        变量值: 任意类型的变量。
        最大展示长度 (int): 内容过长时的截断长度。默认 500。
        启用颜色 (bool): 是否打印彩色文本。默认 True。
        颜色_名称 (str): 对 “变量名称” 这一行使用的颜色，默认 cyan。

    Returns:
        None
    """
    try:
        # --- 内部颜色映射 ---
        映射 = {
            # 基础色
            "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
            "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
            "white": "\033[37m", "gray": "\033[90m",

            # 亮色
            "bright_red": "\033[91m", "bright_green": "\033[92m",
            "bright_yellow": "\033[93m", "bright_blue": "\033[94m",
            "bright_magenta": "\033[95m", "bright_cyan": "\033[96m",
            "bright_white": "\033[97m",

            # 背景
            "bg_red": "\033[41m", "bg_green": "\033[42m", "bg_yellow": "\033[43m",
            "bg_blue": "\033[44m", "bg_magenta": "\033[45m",
            "bg_cyan": "\033[46m", "bg_white": "\033[47m",

            # 样式
            "bold": "\033[1m", "underline": "\033[4m",

            "plain": "",
        }

        # 安全获取颜色码
        def 着色(文本: str, 色: str) -> str:
            if not 启用颜色:
                return 文本
            前缀 = 映射.get(色.lower(), "")
            return f"{前缀}{文本}\033[0m" if 前缀 else 文本

        # 尝试转文本
        try:
            内容 = str(变量值)
        except Exception:
            内容 = "<无法转换为字符串>"

        原长度 = len(内容)
        if 原长度 > 最大展示长度:
            内容 = 内容[:最大展示长度] + f"...（已截断，总长度 {原长度}）"

        # 打印变量名称
        print(着色(f"变量名称：{变量名称}", 颜色_名称))

        # 打印类型
        类型名 = type(变量值).__name__
        print(着色(f"类型：{类型名}", "yellow"))

        # 打印值
        print(着色(f"值：{内容}", "white"))

    except Exception:
        # 不抛异常
        pass