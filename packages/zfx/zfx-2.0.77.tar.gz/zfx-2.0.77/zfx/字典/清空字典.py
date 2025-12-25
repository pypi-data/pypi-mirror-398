from typing import Any, Dict


def 清空字典(数据: Dict[str, Any]) -> bool:
    """
    清空字典中的所有键值对。

    本函数用于对字典执行安全、受控的清空操作，
    等价于标准写法 `dict.clear()`，
    但在类型校验与异常处理上更加稳健。

    设计特性：
        - 若传入对象不是字典类型，不执行任何操作；
        - 原地清空字典，不创建新对象；
        - 不抛出任何异常，适合作为底层工具函数使用；
        - 返回布尔值以明确操作是否成功执行。

    行为说明：
        - 数据为 dict      → 清空所有键值对，返回 True；
        - 数据不是 dict    → 不执行任何操作，返回 False；
        - 空字典            → 仍视为成功，返回 True。

    Args:
        数据 (dict): 需要被清空的字典对象。

    Returns:
        bool:
            True  - 字典已成功清空（或原本为空）；
            False - 传入对象不是字典或发生异常。
    """
    try:
        if not isinstance(数据, dict):
            return False

        数据.clear()
        return True
    except Exception:
        return False
