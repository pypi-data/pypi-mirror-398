from typing import Any, List


def 去除前后空格(序列: List[Any]) -> List[Any]:
    """
    去除序列中每个字符串元素的前后空格。

    功能说明:
        - 对字符串元素执行 strip() 操作。
        - 非字符串元素保持原样。
        - 如果出现异常，返回空列表。
        - 不会修改原序列，返回新的列表。

    Args:
        序列 (list): 要处理的列表。

    Returns:
        list: 去除前后空格后的新列表。如果出现异常，返回空列表。
    """
    try:
        return [元素.strip() if isinstance(元素, str) else 元素 for 元素 in 序列]
    except Exception:
        return []
