from typing import Any, Dict


def 确保包含键(
    数据: Dict[str, Any],
    键: Any,
    默认值: Any = None
) -> bool:
    """
    确保字典中包含指定键；若键不存在，则写入默认值。

    本函数用于对字典结构进行防御性补全，
    保证后续逻辑在访问指定键时不需要反复进行存在性判断。

    设计特性：
        - 若传入对象不是字典类型，不执行任何操作；
        - 键会被统一转换为字符串，以保持与本模块其他函数的行为一致；
        - 当键不存在时，自动写入默认值；
        - 当键已存在时，不修改原有值；
        - 不抛出任何异常，适合作为底层结构保障函数使用。

    行为说明：
        - 数据为 dict 且键不存在 → 写入默认值，返回 True；
        - 数据为 dict 且键已存在 → 不做任何修改，返回 False；
        - 数据不是 dict           → 不做任何修改，返回 False。

    Args:
        数据 (dict): 目标字典对象。
        键: 需要确保存在的键，内部将转换为字符串。
        默认值: 当键不存在时写入的默认值。

    Returns:
        bool:
            True  - 键不存在且已成功写入默认值；
            False - 键已存在、数据非法或发生异常。
    """
    try:
        if not isinstance(数据, dict):
            return False

        键名 = str(键)

        if 键名 in 数据:
            return False

        数据[键名] = 默认值
        return True
    except Exception:
        return False
