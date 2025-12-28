from typing import Any


def 到字符串(输入值: Any) -> str:
    """
    将任意输入值转换为字符串（str）。

    Args:
        输入值 (Any):
            需要转换为字符串的值。

    Returns:
        str:
            转换后的字符串。

            - 几乎所有类型的对象都可以转换为字符串，例如：
              数字 → "123"
              列表 → "[1, 2, 3]"
              字典 → "{'a': 1, 'b': 2}"
              None → "None"
            - 如果转换失败，则返回空字符串 ""。
    """
    try:
        return str(输入值)
    except Exception:
        return ""
