from typing import Any, Iterable, List


def 置数据_唯一_批量(
    列表: List[Any],
    值序列: Iterable[Any]
) -> bool:
    """
    将一组值唯一地追加到列表中（就地修改）。

    功能说明：
        - 接收一个列表和一个可迭代的值序列；
        - 逐个检查值是否已存在于列表中；
        - 仅当值不存在时才追加；
        - 修改的是传入的原列表对象；
        - 全部流程完成返回 True；
        - 参数非法或异常返回 False；
        - 不抛异常、不打印日志，适合作为底层操作型工具函数。

    Args:
        列表 (list): 需要被修改的列表对象。
        值序列 (Iterable): 需要追加的值序列（list / tuple / set 等）。

    Returns:
        bool:
            - True  ：处理完成
            - False ：失败（列表或值序列非法，或发生异常）
    """
    try:
        if not isinstance(列表, list):
            return False

        for 值 in 值序列:
            if 值 not in 列表:
                列表.append(值)

        return True
    except Exception:
        return False
