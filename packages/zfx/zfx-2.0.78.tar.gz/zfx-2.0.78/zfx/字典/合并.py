from typing import Any, Dict


def 合并(
    目标字典: Dict[str, Any],
    来源字典: Dict[str, Any]
) -> bool:
    """
    将来源字典中的键值对合并到目标字典中。

    本函数用于对字典执行安全、受控的合并操作，
    等价于 Python 原生的 `dict.update()`，
    但在类型校验与异常处理上更加稳健。

    设计特性：
        - 若目标对象不是字典类型，不执行任何操作；
        - 若来源对象不是字典类型，不执行任何操作；
        - 合并操作为原地修改，不创建新的字典对象；
        - 当键在目标字典中已存在时，其值将被来源字典中的值覆盖；
        - 不抛出任何异常，适合作为底层基础工具函数使用。

    行为说明：
        - 目标字典与来源字典均为 dict → 执行合并并返回 True；
        - 任一参数不是 dict              → 不执行合并，返回 False；
        - 来源字典为空                  → 不修改目标字典，返回 True。

    Args:
        目标字典 (dict): 接收合并结果的目标字典。
        来源字典 (dict): 提供键值对的来源字典。

    Returns:
        bool:
            True  - 合并操作已成功执行（或来源为空）；
            False - 参数非法或发生异常。
    """
    try:
        if not isinstance(目标字典, dict):
            return False

        if not isinstance(来源字典, dict):
            return False

        目标字典.update(来源字典)
        return True
    except Exception:
        return False
