from typing import Any, List


def 去除重复(序列: List[Any]) -> List[Any]:
    """
    去除序列中的重复元素，并保持原有顺序。

    功能说明:
        - 使用顺序稳定的方式进行去重。
        - 仅保留首次出现的元素，后续重复元素将被忽略。
        - 如果出现异常，返回空列表。

    Args:
        序列 (list): 包含元素的列表。

    Returns:
        list: 去重后的新列表。如果出现异常，返回空列表。
    """
    try:
        已见 = set()
        新列表 = []
        for 元素 in 序列:
            if 元素 not in 已见:
                已见.add(元素)
                新列表.append(元素)
        return 新列表
    except Exception:
        return []