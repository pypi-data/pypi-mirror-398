from typing import Any, Dict


def 删除键(
    数据: Dict[str, Any],
    键: Any
) -> bool:
    """
    从字典中安全地删除指定键。

    本函数用于对字典执行受控的键删除操作，
    以避免直接使用 `del dict[key]` 或 `pop(key)` 时
    可能引发的 KeyError 或类型异常。

    设计特性：
        - 若传入对象不是字典类型，不执行删除操作；
        - 键会被统一转换为字符串后再进行处理，
          以确保与写入、读取、判断逻辑保持一致；
        - 当键不存在时，不抛出异常，直接返回 False；
        - 不抛出任何异常，适合作为底层字典工具函数使用。

    行为说明：
        - 数据为 dict 且键存在     → 删除该键并返回 True；
        - 数据为 dict 但键不存在   → 不执行任何操作，返回 False；
        - 数据不是 dict            → 不执行任何操作，返回 False。

    Args:
        数据 (dict): 目标字典对象。
        键: 需要删除的键，内部将转换为字符串。

    Returns:
        bool:
            True  - 键存在且已成功删除；
            False - 键不存在、数据非法或发生异常。
    """
    try:
        if not isinstance(数据, dict):
            return False

        键名 = str(键)

        if 键名 not in 数据:
            return False

        del 数据[键名]
        return True
    except Exception:
        return False