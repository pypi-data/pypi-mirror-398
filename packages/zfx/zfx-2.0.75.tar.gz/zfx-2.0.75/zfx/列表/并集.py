from typing import Any, List, Tuple


def 并集(序列1: List[Any], 序列2: List[Any]) -> Tuple[List[Any], bool]:
    """
    获取两个序列的并集（顺序稳定）。

    功能说明:
        - 返回两个序列中所有不同元素组成的新序列。
        - 顺序保持为：序列1 的顺序 + 序列2 中未出现过的元素顺序。
        - 不修改原序列。
        - 成功返回 (并集列表, True)，失败返回 ([], False)。

    Args:
        序列1 (list): 第一个序列。
        序列2 (list): 第二个序列。

    Returns:
        tuple:
            - list: 并集后的新序列。若失败则为空列表。
            - bool: 是否成功。
    """
    try:
        已见 = set()
        结果 = []

        # 遍历序列1
        for 元素 in 序列1:
            if 元素 not in 已见:
                已见.add(元素)
                结果.append(元素)

        # 遍历序列2
        for 元素 in 序列2:
            if 元素 not in 已见:
                已见.add(元素)
                结果.append(元素)

        return 结果, True
    except Exception:
        return [], False
