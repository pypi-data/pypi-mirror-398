from typing import Any, List


def 验证_全为数字(序列: List[Any]) -> bool:
    """
    验证序列中的所有元素是否都是数字。

    功能说明:
        - 判断序列中每个元素是否属于数字类型（int、float）。
        - 只要出现一个非数字，整体返回 False。
        - 所有元素都是数字则返回 True。
        - bool 类型不视为数字（避免 True/False 被当成 1/0）。
        - 遇到异常也返回 False。

    Args:
        序列 (list): 需要验证的序列。

    Returns:
        bool: 若全部为数字返回 True，否则返回 False。
    """
    try:
        for 元素 in 序列:
            if isinstance(元素, bool):
                return False

            if not isinstance(元素, (int, float)):
                return False

        return True

    except Exception:
        return False
