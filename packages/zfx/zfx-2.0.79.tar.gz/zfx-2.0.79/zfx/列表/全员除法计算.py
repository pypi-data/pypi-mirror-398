from typing import Any, List, Union


def 全员除法计算(序列: List[Any], 除数: Union[int, float]) -> List[float]:
    """
    将序列中的每个数字元素都除以指定的数值。

    功能说明:
        - 仅处理数字元素（int 或 float）。
        - 如果序列中包含非数字元素，返回空列表。
        - 如果除数为 0，返回空列表。
        - 不修改原序列。

    Args:
        序列 (list): 包含数字的列表。
        除数 (int | float): 用于除以每个数字元素的数值。

    Returns:
        list: 所有数字元素除以指定数值后的结果。如果出现任何异常，返回空列表。
    """
    try:
        if 除数 == 0:
            return []

        新列表 = []
        for 元素 in 序列:
            if isinstance(元素, (int, float)):
                新列表.append(元素 / 除数)
            else:
                return []
        return 新列表
    except Exception:
        return []
