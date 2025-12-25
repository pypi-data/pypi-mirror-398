from typing import Any, Dict, List


def 值转列表(数据: Dict[str, Any]) -> List[Any]:
    """
    将字典中的所有值提取为列表。

    本函数用于安全地获取字典的值集合，并以列表形式返回，
    以替代直接使用 `dict.values()` 等方式，
    从而避免因数据类型不正确而引发异常。

    设计特性：
        - 若传入对象不是字典类型，直接返回空列表；
        - 保持值的原始类型与结构，不做任何修改或拷贝；
        - 返回的是一个新的列表对象，不会影响原字典结构；
        - 不抛出任何异常，适合作为底层通用工具函数使用。

    行为说明：
        - 数据为 dict            → 返回包含所有值的列表；
        - 数据不是 dict          → 返回空列表；
        - 空字典                → 返回空列表。

    Args:
        数据 (dict): 用于提取值的字典对象。

    Returns:
        list:
            - 成功：包含字典中所有值的列表；
            - 失败：空列表。
    """
    try:
        if not isinstance(数据, dict):
            return []

        return list(数据.values())
    except Exception:
        return []