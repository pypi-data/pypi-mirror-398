from typing import Any, List


def 验证_无空元素(序列: List[Any]) -> bool:
    """
    验证序列中是否不存在空元素。

    功能说明:
        - 判断序列中的每个元素是否为“非空”。
        - 以下情况视为“空”：
            · None
            · 空字符串 ""
            · 空列表 []
            · 空字典 {}
            · 空元组 ()
            · 空集合 set()
        - 数字 0 和布尔 False 不视为空。
        - 任意一个元素为空则返回 False。
        - 所有元素都非空则返回 True。
        - 遇到异常返回 False。

    Args:
        序列 (list): 需要验证的序列。

    Returns:
        bool: 若所有元素都非空返回 True，否则返回 False。
    """
    try:
        for 元素 in 序列:
            # 特别排除数字 zero 和 False（它们不是“空”，只是值为 False）
            if 元素 is None:
                return False

            if 元素 == "" or 元素 == [] or 元素 == {} or 元素 == () or 元素 == set():
                return False

        return True

    except Exception:
        return False
