from typing import Any, List


def 置数据_索引_替换(
    列表: List[Any],
    索引: int,
    值: Any
) -> bool:
    """
    按指定索引位置替换列表中的值（就地修改）。

    功能说明：
        - 接收一个列表、一个索引位置和一个任意类型的值；
        - 使用索引赋值的方式覆盖原有元素；
        - 列表长度保持不变；
        - 修改的是传入的原列表对象；
        - 成功返回 True；
        - 参数非法、索引越界或异常返回 False；
        - 不抛异常、不打印日志，适合作为底层操作型工具函数。

    Args:
        列表 (list): 需要被修改的列表对象。
        索引 (int): 要替换的索引位置（支持负索引）。
        值 (Any): 用于替换的新值，类型不做限制。

    Returns:
        bool:
            - True  ：替换成功
            - False ：失败（列表或索引非法，或索引越界）
    """
    try:
        if not isinstance(列表, list):
            return False

        if not isinstance(索引, int):
            return False

        列表[索引] = 值
        return True
    except Exception:
        return False
