from typing import Any, List, Tuple


def 分割为固定大小(序列: List[Any], 大小: int) -> Tuple[List[List[Any]], bool]:
    """
    将序列按指定大小分割为多个子序列（不修改原序列）。

    功能说明:
        - 按固定大小将原列表切分成多个小列表。
        - 若最后一段长度不足指定大小，仍会作为一个子列表返回。
        - 若大小 <= 0，返回空列表。
        - 原序列保持不变。

    Args:
        序列 (list): 要分割的原始序列。
        大小 (int): 每个子序列的目标长度。

    Returns:
        list: 由子列表组成的新列表；失败时为空列表。
        bool: 是否成功；成功 True，失败 False。
    """
    try:
        if 大小 <= 0:
            return [], True

        结果: List[List[Any]] = []
        长度 = len(序列)

        # 步长切片
        for i in range(0, 长度, 大小):
            结果.append(序列[i:i + 大小])

        return 结果, True

    except Exception:
        return [], False