from typing import Any, List


def 验证_全为同类型(序列: List[Any]) -> bool:
    """
    验证序列中的所有元素是否都属于同一种类型。

    功能说明:
        - 以第一个元素的类型作为对照标准。
        - 序列中每个元素都必须与第一个元素的类型一致。
        - Python 的类型比较采用 type()，需要完全相同才通过：
            · 例如 1（int） 与 True（bool）类型不同，视为不通过。
            · 例如 [1,2]（list） 与 [3,4]（list）类型相同，通过。
        - 序列为空或只有一个元素时，视为类型一致。
        - 若出现异常，返回 False。

    Args:
        序列 (list): 需要验证的序列。

    Returns:
        bool: 若所有元素类型一致返回 True，否则返回 False。
    """
    try:
        if len(序列) <= 1:
            return True

        基准类型 = type(序列[0])

        for 元素 in 序列:
            if type(元素) is not 基准类型:
                return False

        return True

    except Exception:
        return False
