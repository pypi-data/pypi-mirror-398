from typing import Any


def 到逻辑型(输入值: Any) -> bool:
    """
    将输入值转换为布尔值（逻辑型）。

    Args:
        输入值 (Any):
            需要转换为布尔值的值。

    Returns:
        bool:
            转换后的布尔值。

            - 以下值会被视为 False：
              0、0.0、空字符串 ""、空列表 []、空字典 {}、None。
              字符串形式的 "false"、"no"、"n"、"off"、"0"（不区分大小写）。
            - 其他任何非空或非零值会被视为 True。
            - 如果转换失败或输入异常，则返回 False。
    """
    try:
        if isinstance(输入值, str):
            值 = 输入值.strip().lower()
            if 值 in ("false", "no", "n", "off", "0", ""):
                return False
            if 值 in ("true", "yes", "y", "on", "1"):
                return True
            # 其他非空字符串默认 True
            return True

        # 对于非字符串类型，使用 Python 标准 bool() 逻辑
        return bool(输入值)

    except Exception:
        return False
