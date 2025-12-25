from typing import Any, List, Tuple


def 筛选_关键词过滤(序列: List[Any], 关键词: str) -> Tuple[List[Any], bool]:
    """
    过滤掉序列中包含指定关键词的元素。

    功能说明:
        - 每个元素会先转换为字符串再进行关键词判断。
        - 成功返回 (新序列, True)，失败返回 ([], False)。

    Args:
        序列 (list): 要处理的序列。
        关键词 (str): 要过滤掉的关键词。

    Returns:
        tuple:
            - 新序列 (list): 不包含关键词的元素列表；失败时为空列表。
            - 成功 (bool): 成功返回 True，失败返回 False。
    """
    try:
        新序列 = [元素 for 元素 in 序列 if 关键词 not in str(元素)]
        return 新序列, True
    except Exception:
        return [], False
