from typing import Any, List, Tuple


def 筛选_最小长度过滤(序列: List[Any], 最小长度: int) -> Tuple[List[Any], bool]:
    """
    过滤掉序列中长度小于指定最小值的元素。

    功能说明:
        - 支持字符串或任何可计算长度的元素。
        - 无法计算长度的元素会被自动过滤。
        - 成功返回 (新序列, True)，失败返回 ([], False)。

    Args:
        序列 (list): 要处理的序列。
        最小长度 (int): 允许保留的最小长度。

    Returns:
        tuple:
            - 新序列 (list): 过滤后的结果；失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        新序列 = []
        for 元素 in 序列:
            try:
                if len(元素) >= 最小长度:
                    新序列.append(元素)
            except Exception:
                # 无法计算长度的元素直接过滤
                continue

        return 新序列, True
    except Exception:
        return [], False
