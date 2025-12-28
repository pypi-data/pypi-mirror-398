from typing import Any, List, Callable, Tuple


def 排序_key(序列: List[Any], key函数: Callable[[Any], Any]) -> Tuple[List[Any], bool]:
    """
    根据 key 函数对序列排序（不修改原序列）。

    功能说明:
        - 按照 key 函数返回的值进行排序。
        - 返回排序后的新列表，原序列保持不变。
        - 序列可以是数字、字符串、字典等任意类型。

    Args:
        序列 (list): 需要排序的列表。
        key函数 (callable): 提供排序依据的函数，例如：
            - key=lambda x: x["price"]       （按字典的 price 排）
            - key=lambda x: len(x)           （按长度排）
            - key=lambda x: x.lower()        （按小写字母排序）

    Returns:
        tuple:
            - list: 排好序的列表；失败则为空列表。
            - bool: 成功返回 True，失败返回 False。

    示例:
        1) 序列中是字典，按价格排序：
            原序列 = [{"p": 30}, {"p": 10}, {"p": 20}]
            排序_key(原序列, key函数=lambda x: x["p"])
            返回结果 = [{"p": 10}, {"p": 20}, {"p": 30}]

        2) 序列中是字符串，按长度排序：
            原序列 = ["apple", "hi", "cat"]
            排序_key(原序列, key函数=lambda x: len(x))
            返回结果 = ["hi", "cat", "apple"]

        3) 序列中是字符串，忽略大小写排序：
            原序列 = ["Zoo", "apple", "Banana"]
            排序_key(原序列, key函数=lambda x: x.lower())
            返回结果 = ["apple", "Banana", "Zoo"]
    """
    try:
        新列表 = sorted(序列, key=key函数)
        return 新列表, True
    except Exception:
        return [], False