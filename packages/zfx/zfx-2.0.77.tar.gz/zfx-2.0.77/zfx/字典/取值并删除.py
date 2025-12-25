from typing import Any, Dict


def 取值并删除(
    数据: Dict[str, Any],
    键: Any,
    默认值: Any = None
) -> Any:
    """
    从字典中取出指定键对应的值，并同时将该键从字典中删除。

    本函数用于对字典执行安全的“读取 + 删除”复合操作，
    等价于 Python 原生的 `dict.pop(key, default)`，
    但在类型校验与异常处理上更加稳健。

    设计特性：
        - 若传入对象不是字典类型，直接返回默认值；
        - 键会被统一转换为字符串，以保持与本模块中其他函数的键语义一致；
        - 当键不存在时，不抛出 KeyError，而是返回默认值；
        - 操作为原地修改，不创建新的字典对象；
        - 不抛出任何异常，适合作为底层基础工具函数使用。

    行为说明：
        - 数据为 dict 且键存在     → 返回对应值，并删除该键；
        - 数据为 dict 但键不存在   → 返回默认值，不做任何修改；
        - 数据不是 dict            → 返回默认值，不做任何修改。

    Args:
        数据 (dict): 目标字典对象。
        键: 需要取值并删除的键，内部将转换为字符串。
        默认值: 当键不存在或操作失败时返回的值。

    Returns:
        Any:
            - 成功：返回被删除键对应的原始值；
            - 失败：返回默认值。
    """
    try:
        if not isinstance(数据, dict):
            return 默认值

        键名 = str(键)

        if 键名 not in 数据:
            return 默认值

        return 数据.pop(键名)
    except Exception:
        return 默认值
