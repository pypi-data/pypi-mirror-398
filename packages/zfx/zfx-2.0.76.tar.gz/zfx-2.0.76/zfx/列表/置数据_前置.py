from typing import Any, List


def 置数据_前置(
    列表: List[Any],
    值: Any
) -> bool:
    """
    将给定值插入到列表最前面（就地修改）。

    功能说明：
        - 接收一个列表和一个任意类型的值；
        - 将值插入到列表索引 0 的位置；
        - 修改的是传入的原列表对象；
        - 成功返回 True；
        - 参数非法或异常返回 False；
        - 不抛异常、不打印日志，适合作为底层操作型工具函数。

    Args:
        列表 (list): 需要被修改的列表对象。
        值 (Any): 要前置插入的值，类型不做限制。

    Returns:
        bool:
            - True  ：插入成功
            - False ：失败（列表不是 list 或发生异常）
    """
    try:
        if not isinstance(列表, list):
            return False

        列表.insert(0, 值)
        return True
    except Exception:
        return False