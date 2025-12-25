from typing import Any, List, Union


def 全员加法计算(序列: List[Any], 加数: Union[int, float]) -> List[float]:
    """
    将序列中的每个数字元素都加上指定的数值。

    功能说明:
        - 仅处理数字元素（int 或 float）。
        - 如果序列中出现非数字元素，则返回空列表。
        - 不会修改原序列，返回新的列表。

    Args:
        序列 (list): 包含数字的列表。
        加数 (int | float): 需要加到每个数字元素上的数值。

    Returns:
        list: 所有元素加上指定值后的新列表。如果出现任何异常，返回空列表。
    """
    try:
        新列表 = []
        for 元素 in 序列:
            if isinstance(元素, (int, float)):
                新列表.append(元素 + 加数)
            else:
                return []
        return 新列表
    except Exception:
        return []
