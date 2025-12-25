from typing import Any, List


def 验证_无重复元素(序列: List[Any]) -> bool:
    """
    验证序列中是否不存在重复元素。

    功能说明:
        - 判断序列中是否所有元素都唯一，不存在重复项。
        - 对可哈希元素（如数字、字符串、元组）使用 set 加速判断。
        - 对不可哈希类型（如 list、dict）会退回逐个比较的方式。
        - 遇到以下情况视为“有重复”：
            · 元素内容完全相同（例如两个相同的字典）
            · 数字 1 与布尔 True 因值相同视为重复
        - 若序列为空或只有一个元素，则一定唯一。
        - 遇到异常返回 False。

    Args:
        序列 (list): 需要验证的序列。

    Returns:
        bool: 若所有元素都唯一返回 True，否则返回 False。
    """
    try:
        # 若全为可哈希元素（如数字、字符串、元组）可直接使用 set 判断
        try:
            if len(set(序列)) == len(序列):
                return True
            else:
                return False
        except Exception:
            # 存在不可哈希元素（如 list / dict），改用逐项比较
            已见 = []
            for 元素 in 序列:
                if 元素 in 已见:
                    return False
                已见.append(元素)
            return True

    except Exception:
        return False
