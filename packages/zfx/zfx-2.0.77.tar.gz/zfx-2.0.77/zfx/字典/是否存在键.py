from typing import Any, Dict


def 是否存在键(
    数据: Dict[str, Any],
    键: Any
) -> bool:
    """
    判断指定键是否存在于字典中。

    本函数用于对字典执行安全、确定的键存在性判断，
    以替代直接使用 `key in dict` 所可能引发的类型问题。

    设计特性：
        - 若传入对象不是字典类型，直接返回 False；
        - 键会被统一转换为字符串后再进行判断，
          以确保与写入、读取逻辑保持一致；
        - 不抛出任何异常，适合作为条件判断的基础工具函数。

    行为说明：
        - 数据为 dict 且键存在     → 返回 True；
        - 数据为 dict 但键不存在   → 返回 False；
        - 数据不是 dict            → 返回 False。

    Args:
        数据 (dict): 用于判断的字典对象。
        键: 需要判断是否存在的键，内部将转换为字符串。

    Returns:
        bool:
            True  - 键存在于字典中；
            False - 键不存在、数据非法或发生异常。
    """
    try:
        if not isinstance(数据, dict):
            return False

        return str(键) in 数据
    except Exception:
        return False