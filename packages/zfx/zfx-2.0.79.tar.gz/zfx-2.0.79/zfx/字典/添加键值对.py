from typing import Any, Dict


def 添加键值对(
    数据: Dict[str, Any],
    键: Any,
    值: Any
) -> bool:
    """
    向给定字典中添加或更新一个键值对。

    本函数用于对字典执行最基础且安全的写入操作，等价于：
        数据[键] = 值

    设计特性：
        - 若传入对象不是字典类型，将直接返回 False，不执行任何写入操作；
        - 键会被强制转换为字符串，以确保字典结构在 JSON 序列化、
          数据库存储及跨系统传输时保持稳定；
        - 值不做任何修改或类型限制，可为任意 Python 对象；
        - 不抛出异常，适合作为底层工具函数在任何环境中调用。

    行为说明：
        - 当键不存在时：新增键值对；
        - 当键已存在时：覆盖原有值；
        - 覆盖行为符合 Python 原生 dict 的标准语义。

    Args:
        数据 (dict): 目标字典对象，必须为可变字典。
        键: 要添加或更新的键，内部将统一转换为字符串。
        值: 要写入字典的值，类型不限。

    Returns:
        bool:
            - True  ：键值对成功写入字典；
            - False ：传入对象不是字典或发生异常。
    """
    try:
        if not isinstance(数据, dict):
            return False

        数据[str(键)] = 值
        return True
    except Exception:
        return False