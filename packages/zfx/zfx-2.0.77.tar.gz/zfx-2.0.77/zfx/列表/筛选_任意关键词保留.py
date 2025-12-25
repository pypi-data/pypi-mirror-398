from typing import Any, List, Tuple


def 筛选_任意关键词保留(序列: List[Any], 关键词列表: List[str]) -> Tuple[List[Any], bool]:
    """
    从序列中筛选出包含任意一个关键词的元素（OR 条件，不修改原序列）。

    功能说明:
        - 遍历整个序列，判断每个元素是否包含任意关键词。
        - 元素会被统一转成字符串进行匹配，避免类型不一致导致报错。
        - 关键词匹配采用“只要命中其一就保留”的 OR 逻辑。
        - 若关键词列表为空，则返回空列表（无条件匹配）。

    Args:
        序列 (list): 要筛选的原始序列。
        关键词列表 (list[str]): 多个关键词组成的列表。

    Returns:
        list: 只保留匹配任意关键词的元素；失败时为空列表。
        bool: 是否成功；成功为 True，失败为 False。
    """
    try:
        if not isinstance(关键词列表, list) or not 关键词列表:
            return [], True  # 无关键词直接返回空结果

        结果 = []
        for 元素 in 序列:
            文本 = str(元素)
            for 词 in 关键词列表:
                if 词 in 文本:
                    结果.append(元素)
                    break  # 已命中任一关键词，直接保留

        return 结果, True

    except Exception:
        return [], False