from typing import Iterable, SupportsFloat, Optional, List


def 求极差(数据序列: Iterable[SupportsFloat]) -> Optional[float]:
    """
    计算数值序列的极差（最大值与最小值之差）。

    功能说明：
        - 自动将所有元素转换为 float。
        - 若序列为空、无法转换或包含非法值，返回 None。
        - 极差用于衡量数据的分布范围。

    Args:
        数据序列 (Iterable[SupportsFloat]): 任意可迭代的数值序列。

    Returns:
        float | None:
            - 成功：返回极差（float）
            - 失败：返回 None

    Notes:
        - 极差 = max(序列) - min(序列)
    """
    try:
        数列: List[float] = [float(x) for x in 数据序列]
        if not 数列:
            return None
        return max(数列) - min(数列)
    except Exception:
        return None
