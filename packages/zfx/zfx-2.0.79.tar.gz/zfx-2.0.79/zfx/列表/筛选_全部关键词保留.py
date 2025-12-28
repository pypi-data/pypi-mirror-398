from typing import Any, List, Tuple


def 筛选_全部关键词保留(序列: List[Any], 关键词列表: List[str]) -> Tuple[List[Any], bool]:
    """
    从序列中筛选出必须包含所有关键词的元素（AND 条件，不修改原序列）。

    功能说明:
        - 元素会统一转成字符串进行关键词匹配。
        - 所有关键词都必须在元素文本中出现才会被保留。
        - 若关键词列表为空，返回空列表（无条件无法判断）。
        - 原序列保持不变。

    Args:
        序列 (list): 要筛选的原始序列。
        关键词列表 (list[str]): 多个关键词组成的列表，每个都必须命中。

    Returns:
        list: 只保留同时包含所有关键词的元素；失败时为空列表。
        bool: 是否成功；成功为 True，失败为 False。
    """
    try:
        if not isinstance(关键词列表, list) or not 关键词列表:
            return [], True  # 没关键词，无筛选意义，返回空列表

        结果 = []
        for 元素 in 序列:
            文本 = str(元素)

            # 使用 all() 判断所有关键词都必须出现
            if all(词 in 文本 for 词 in 关键词列表):
                结果.append(元素)

        return 结果, True

    except Exception:
        return [], False
