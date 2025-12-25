from typing import Any, Dict, Iterable


def 只保留键(
    数据: Dict[str, Any],
    保留键列表: Iterable[Any]
) -> Dict[str, Any]:
    """
    根据给定的键列表，仅保留字典中对应的键值对。

    本函数用于对字典结构进行裁剪，
    返回一个只包含指定键的新字典，不会修改原始字典。

    设计特性：
        - 若传入对象不是字典类型，返回空字典；
        - 所有用于匹配的键都会统一转换为字符串，
          以保证与本模块中其他函数的键处理规则一致；
        - 不存在于原字典中的键会被自动忽略；
        - 返回的是一个新的字典对象，不影响原始数据；
        - 不抛出任何异常，适合作为底层结构处理工具函数使用。

    行为说明：
        - 数据为 dict：
            - 仅保留「原字典中存在」且「在保留键列表中」的键；
            - 其余键全部丢弃；
        - 数据不是 dict → 返回 {}；
        - 保留键列表为空 → 返回 {}。

    Args:
        数据 (dict): 原始字典对象。
        保留键列表 (Iterable): 需要保留的键集合。

    Returns:
        dict:
            - 成功：仅包含指定键的新字典；
            - 失败：空字典 {}。
    """
    try:
        if not isinstance(数据, dict):
            return {}

        if not 保留键列表:
            return {}

        目标键集合 = {str(键) for 键 in 保留键列表}

        return {
            str(键): 值
            for 键, 值 in 数据.items()
            if str(键) in 目标键集合
        }
    except Exception:
        return {}