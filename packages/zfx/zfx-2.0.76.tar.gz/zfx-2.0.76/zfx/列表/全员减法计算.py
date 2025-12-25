from typing import Any, List, Union


def 全员减法计算(序列: List[Any], 减数: Union[int, float]) -> List[float]:
    """
    将序列中的每个数字元素都减去指定数值，返回新序列。

    功能说明:
        - 仅处理数字元素（int 或 float）。
        - 如果序列中存在非数字元素，则返回空列表。
        - 不修改原序列，返回一个新的列表。

    Args:
        序列 (list): 包含数字的列表。
        减数 (int | float): 要从每个数字元素减去的数值。

    Returns:
        list: 所有元素减去指定值后的新列表。如果出现任何异常，返回空列表。
    """
    try:
        新列表 = []
        for 元素 in 序列:
            if isinstance(元素, (int, float)):
                新列表.append(元素 - 减数)
            else:
                return []
        return 新列表
    except Exception:
        return []