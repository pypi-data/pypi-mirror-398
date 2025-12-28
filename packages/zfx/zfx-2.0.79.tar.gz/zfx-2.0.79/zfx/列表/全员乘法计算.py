from typing import Any, List, Union


def 全员乘法计算(序列: List[Any], 乘数: Union[int, float]) -> List[float]:
    """
    将序列中的所有数字元素与指定数值相乘。

    功能说明:
        - 仅处理数字元素（int 或 float）。
        - 如果序列中存在非数字元素，则返回空列表。
        - 本函数不会修改原序列。

    Args:
        序列 (list): 包含数字的列表。
        乘数 (int | float): 用于乘以每个数字元素的数值。

    Returns:
        list: 所有元素相乘后的新列表。如果处理失败或出现异常，返回空列表。
    """
    try:
        新列表 = []
        for 元素 in 序列:
            if isinstance(元素, (int, float)):
                新列表.append(元素 * 乘数)
            else:
                return []
        return 新列表
    except Exception:
        return []