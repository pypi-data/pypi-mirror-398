from typing import Any, List, Tuple


def 筛选_最大长度过滤(序列: List[Any], 最大长度: int) -> Tuple[List[Any], bool]:
    """
    过滤掉序列中长度大于指定最大值的元素。

    功能说明:
        - 支持字符串或任何可计算长度的元素。
        - 对无法计算长度的元素自动过滤。
        - 成功返回 (新序列, True)，失败返回 ([], False)。

    Args:
        序列 (list): 要处理的序列。
        最大长度 (int): 允许保留的最大长度。

    Returns:
        tuple:
            - 新序列 (list): 过滤后的结果；失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        新序列 = []
        for 元素 in 序列:
            try:
                if len(元素) <= 最大长度:
                    新序列.append(元素)
            except Exception:
                # 无法计算长度的元素直接过滤掉
                continue

        return 新序列, True
    except Exception:
        return [], False
