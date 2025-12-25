from typing import Any, List, Tuple


def 按元素数量分组(序列: List[Any], 组大小: int) -> Tuple[List[List[Any]], bool]:
    """
    按指定大小对序列进行分组。

    功能说明:
        - 按组大小切片生成子序列。
        - 成功返回 (分组结果, True)，失败返回 ([], False)。

    Args:
        序列 (list): 要分组的序列。
        组大小 (int): 每个分组的大小。

    Returns:
        tuple:
            - 分组结果 (list): 失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        if 组大小 <= 0:
            return [], False

        分组结果 = [
           序列[i : i + 组大小]
            for i in range(0, len(序列), 组大小)
        ]
        return 分组结果, True
    except Exception:
        return [], False
