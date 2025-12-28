from typing import Any, Dict


def 是否为空(数据: Dict[str, Any]) -> bool:
    """
    判断字典是否为空。

    本函数用于对字典执行安全、明确的空判断，
    以替代直接使用 `len(dict) == 0` 或 `not dict` 等写法，
    从而避免因数据类型不正确而引发异常或歧义。

    设计特性：
        - 若传入对象不是字典类型，直接视为“为空”；
        - 仅判断字典是否包含键值对，不关心值内容；
        - 不抛出任何异常，适合作为条件判断的基础工具函数。

    行为说明：
        - 数据为 dict 且不包含任何键 → 返回 True；
        - 数据为 dict 且包含至少一个键 → 返回 False；
        - 数据不是 dict                → 返回 True。

    设计取舍说明：
        - 将“非字典”视为“为空”，是出于防御性设计考虑；
        - 本函数用于结构判断，而非严格的类型校验；
        - 若需要区分“非字典”与“空字典”，应由上层逻辑处理。

    Args:
        数据 (dict): 需要判断是否为空的字典对象。

    Returns:
        bool:
            True  - 字典为空或数据非法；
            False - 字典非空。
    """
    try:
        if not isinstance(数据, dict):
            return True

        return len(数据) == 0
    except Exception:
        return True
