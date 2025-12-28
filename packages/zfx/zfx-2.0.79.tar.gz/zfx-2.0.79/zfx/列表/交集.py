from typing import Any, List


def 交集(列表1: List[Any], 列表2: List[Any]) -> List[Any]:
    """
    获取两个列表的交集（两个列表都包含的元素）。

    功能说明:
        - 使用集合提高查找性能，但最终结果顺序保持与列表1一致。
        - 如果输入包含不可哈希对象，交集检查会退化为线性比较。

    Args:
        列表1 (list): 第一个列表。
        列表2 (list): 第二个列表。

    Returns:
        list: 包含两个列表中共同元素的列表。如果出现不可预期的异常，返回空列表。
    """
    try:
        try:
            # 优先使用集合（高性能路径）
            集合2 = set(列表2)
            return [元素 for 元素 in 列表1 if 元素 in 集合2]
        except TypeError:
            # 列表含不可哈希元素 → 退化为线性比较（低性能但正确）
            return [元素 for 元素 in 列表1 if 元素 in 列表2]
    except Exception:
        return []
