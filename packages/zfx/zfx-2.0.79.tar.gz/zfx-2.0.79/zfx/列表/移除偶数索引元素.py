from typing import Any, List, Tuple


def 移除偶数索引元素(序列: List[Any]) -> Tuple[List[Any], bool]:
    """
    移除序列中所有偶数索引位置的元素。

    功能说明:
        - 索引从 0 开始，因此移除位置为 0、2、4、6……
        - 成功返回 (新序列, True)，失败返回 ([], False)。

    Args:
        序列 (list): 要处理的序列。

    Returns:
        tuple:
            - 新序列 (list): 移除偶数索引元素后的结果；失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        新序列 = [元素 for 索引, 元素 in enumerate(序列) if 索引 % 2 != 0]
        return 新序列, True
    except Exception:
        return [], False
