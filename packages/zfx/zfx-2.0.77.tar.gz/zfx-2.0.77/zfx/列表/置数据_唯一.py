from typing import Any, List


def 置数据_唯一(
    列表: List[Any],
    值: Any
) -> bool:
    """
    将给定值追加到列表中（唯一性保证，就地修改）。

    功能说明：
        - 接收一个列表和一个任意类型的值；
        - 若该值已存在于列表中，不做任何修改；
        - 若不存在，则追加到列表末尾；
        - 修改的是传入的原列表对象；
        - 成功或无需操作返回 True；
        - 参数非法或异常返回 False。

    Args:
        列表 (list): 需要被修改的列表对象。
        值 (Any): 要追加到列表中的值，类型不做限制。

    Returns:
        bool:
            - True  ：追加成功，或值已存在
            - False ：失败（列表不是 list 或发生异常）
    """
    try:
        if not isinstance(列表, list):
            return False

        if 值 in 列表:
            return True

        列表.append(值)
        return True
    except Exception:
        return False