from typing import Any, List, Tuple


def 排序(序列: List[Any], 逆序: bool = False) -> Tuple[List[Any], bool]:
    """
    对序列进行排序。

    功能说明:
        - 使用 sorted() 进行排序，不修改原序列。
        - 支持升序和逆序。
        - 成功返回 (排序结果, True)，失败返回 ([], False)。

    Args:
        序列 (list): 要排序的序列。
        逆序 (bool): 是否逆序排序，默认 False（升序）。

    Returns:
        tuple:
            - 排序结果 (list): 失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        结果 = sorted(序列, reverse=逆序)
        return 结果, True
    except Exception:
        return [], False
