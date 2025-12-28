from typing import Any, List, Dict


def 统计_频率(序列: List[Any]) -> Dict[Any, int]:
    """
    统计序列中每个元素的出现次数（频率统计）。

    功能说明:
        - 遍历整个序列，对每个元素进行计数。
        - 返回一个字典，键为元素本身，值为出现次数。
        - 支持任意可哈希类型的元素（数字、字符串、元组等）。
        - 若存在不可哈希类型（如 list、dict），会跳过计数。
        - 出现异常时返回空字典。

    Args:
        序列 (list): 要统计的序列。

    Returns:
        dict: 键为元素、值为出现次数的统计结果。
    """
    try:
        结果: Dict[Any, int] = {}
        for 元素 in 序列:
            try:
                结果[元素] = 结果.get(元素, 0) + 1
            except Exception:
                # 不可哈希类型无法用作字典键，直接跳过
                pass
        return 结果
    except Exception:
        return {}
