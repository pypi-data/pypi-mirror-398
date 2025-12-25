from typing import Any, Dict, List, Tuple


def 键值对转列表(数据: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """
    将字典中的所有键值对转换为列表形式返回。

    本函数用于安全地获取字典的键值对集合，
    并以列表形式返回，等价于标准写法 `list(dict.items())`，
    但在类型校验与异常处理上更加稳健。

    设计特性：
        - 若传入对象不是字典类型，直接返回空列表；
        - 所有键在返回前会统一转换为字符串，
          以保证与本模块中写入、读取、判断逻辑保持一致；
        - 值保持原始类型与结构，不做任何修改或拷贝；
        - 返回的是新的列表对象，不影响原字典本身；
        - 不抛出任何异常，适合作为底层通用工具函数使用。

    行为说明：
        - 数据为 dict            → 返回 [(键, 值), ...] 列表；
        - 数据不是 dict          → 返回空列表；
        - 空字典                → 返回空列表。

    Args:
        数据 (dict): 用于提取键值对的字典对象。

    Returns:
        list[tuple[str, Any]]:
            - 成功：包含所有键值对的列表；
            - 失败：空列表。
    """
    try:
        if not isinstance(数据, dict):
            return []

        return [(str(键), 值) for 键, 值 in 数据.items()]
    except Exception:
        return []