from typing import Any, List


def 元素替换(序列: List[Any], 旧元素: Any, 新元素: Any) -> List[Any]:
    """
    将序列中的指定元素替换为新元素。

    功能说明:
        - 使用列表推导式生成新列表，不会修改原序列。
        - 替换规则基于等号比较。

    Args:
        序列 (list): 要处理的列表。
        旧元素 (any): 需要被替换的元素。
        新元素 (any): 用于替换的元素。

    Returns:
        list: 替换后的新列表。如果出现异常，返回空列表。
    """
    try:
        return [新元素 if x == 旧元素 else x for x in 序列]
    except TypeError:
        # 传入了不可迭代对象
        return []
    except Exception:
        # 捕获极少见的边界错误
        return []