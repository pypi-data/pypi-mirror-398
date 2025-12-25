from typing import Any


def 到小数(输入值: Any) -> float:
    """
    将输入值转换为小数（浮点数）。

    Args:
        输入值 (Any):
            需要转换为小数的值。

    Returns:
        float:
            转换后的浮点数。

            - 可成功转换的示例：
              数字类型（如 1、3.14）
              字符串形式的数字（如 "5"、"2.718"）
            - 如果输入值无法转换（如字典、列表、None 等），则返回 0.0。
            - 转换时自动忽略前后空格。
    """
    try:
        # 允许字符串形式数字（如 " 3.14 "）
        return float(str(输入值).strip())
    except Exception:
        return 0.0
