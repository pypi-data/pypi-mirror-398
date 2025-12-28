from typing import Any, List


def 置数据_索引(
    列表: List[Any],
    索引: int,
    值: Any
) -> bool:
    """
    在指定索引位置插入值（就地修改列表）。

    功能说明：
        - 接收一个列表、一个索引位置和一个任意类型的值；
        - 使用 insert 在指定索引位置插入值；
        - 修改的是传入的原列表对象；
        - 成功返回 True；
        - 参数非法或异常返回 False；
        - 不抛异常、不打印日志，适合作为底层操作型工具函数。

    Args:
        列表 (list): 需要被修改的列表对象。
        索引 (int): 插入位置索引（允许负数索引）。
        值 (Any): 要插入的值，类型不做限制。

    Returns:
        bool:
            - True  ：插入成功
            - False ：失败（列表或索引非法，或发生异常）
    """
    try:
        if not isinstance(列表, list):
            return False

        if not isinstance(索引, int):
            return False

        列表.insert(索引, 值)
        return True
    except Exception:
        return False