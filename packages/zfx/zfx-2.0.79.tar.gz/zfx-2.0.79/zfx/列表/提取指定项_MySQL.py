from typing import Any, List, Tuple


def 提取指定项_MySQL(序列: List[Tuple[Any, ...]], 索引: int) -> List[Any]:
    """
    从序列中的每个元组或列表中提取指定索引位置的元素，组成新列表。

    功能说明:
        - 专用于处理 MySQL 查询结果等结构：
            [(a, b), (c, d), ...] → 提取 index=1 → [b, d]
        - 若子项不是可索引类型，或该索引不存在，则跳过该子项。
        - 结果始终为扁平化列表，不修改原序列。
        - 异常安全：任何错误都会被忽略，只影响当前子项。

    Args:
        序列 (list): 通常为 MySQL 查询返回的数据结构（列表中包含元组）。
        索引 (int): 需要提取的元素索引位置。

    Returns:
        list: 包含所有成功提取到的元素的新列表。
    """
    try:
        结果: List[Any] = []
        for 子项 in 序列:
            try:
                值 = 子项[索引]
                结果.append(值)
            except Exception:
                # 子项不是元组/列表 或 索引不存在 → 跳过
                continue
        return 结果

    except Exception:
        return []