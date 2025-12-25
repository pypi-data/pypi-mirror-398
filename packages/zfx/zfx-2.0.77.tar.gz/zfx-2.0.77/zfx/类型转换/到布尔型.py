from typing import Any


def 到布尔型(输入值: Any) -> bool:
    """
    将输入值转换为布尔值（True 或 False）。

    Args:
        输入值 (Any):
            需要转换为布尔值的值。

    Returns:
        bool:
            转换后的布尔值。

            - Python 中以下情况会被视为 False：
              0、0.0、空字符串 ""、空列表 []、空字典 {}、None。
            - 其他任何非空或非零值都被视为 True。
            - 注意：字符串 "False"、"0" 虽然看似代表假，但由于非空，仍为 True。
            - 如果转换过程中出现异常，则返回 False。
    """
    try:
        return bool(输入值)
    except Exception:
        return False
