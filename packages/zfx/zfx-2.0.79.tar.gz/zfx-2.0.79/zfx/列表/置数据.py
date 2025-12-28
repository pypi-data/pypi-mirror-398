from typing import Any, List


def 置数据(
    列表: List[Any],
    值: Any
) -> bool:
    """
    将给定值追加到列表中（就地修改）。

    功能说明：
        - 接收一个列表和一个任意类型的值；
        - 将值直接追加到原列表末尾；
        - 修改的是传入的原列表对象；
        - 成功返回 True，失败返回 False；
        - 不抛异常、不打印日志，适合作为底层操作型工具函数。

    Args:
        列表 (list): 需要被修改的列表对象。
        值 (Any): 要追加到列表中的值，类型不做限制。

    Returns:
        bool:
            - True  ：追加成功
            - False ：失败（列表不是 list 或发生异常）
    """
    try:
        if not isinstance(列表, list):
            return False

        列表.append(值)
        return True
    except Exception:
        return False