from typing import Any, List, Tuple


def 成员合并(序列: List[Any], 连接符号: str) -> Tuple[str, bool]:
    """
    将序列中的每个元素转换为字符串，并使用指定的连接符号连接。

    功能说明:
        - 所有元素会先转换为字符串。
        - 成功返回 (合并字符串, True)，失败返回 ("", False)。

    Args:
        序列 (list): 包含元素的序列。
        连接符号 (str): 用于连接元素的字符串。

    Returns:
        tuple:
            - 合并字符串 (str): 失败时为空字符串。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        return 连接符号.join(str(元素) for 元素 in 序列), True
    except Exception:
        return "", False