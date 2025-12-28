from typing import Any, List, Tuple


def 删除索引区间(序列: List[Any], 起: int, 止: int) -> Tuple[List[Any], bool]:
    """
    删除序列中指定索引范围的元素（不修改原序列）。

    功能说明:
        - 删除从索引“起”到“止”之间的所有元素，采用左闭右开的区间规则：
            起 包含，止 不包含，即 [起, 止)
        - 若“起”或“止”超过序列长度，会自动按有效范围裁剪。
        - 支持负索引，会先按 Python 默认规则转换成正索引。
        - 参数不合理（如起 >= 止）时，返回原序列的拷贝。

    Args:
        序列 (list): 原始序列。
        起 (int): 开始删除的索引位置（包含）。
        止 (int): 停止删除的索引位置（不包含）。

    Returns:
        list: 删除指定区间后的新序列；失败时为空列表。
        bool: 是否成功；成功为 True，失败为 False。
    """
    try:
        长度 = len(序列)

        # 处理负索引
        if 起 < 0:
            起 += 长度
        if 止 < 0:
            止 += 长度

        # 防止越界
        起 = max(0, min(起, 长度))
        止 = max(0, min(止, 长度))

        # 若区间无效，直接返回原序列拷贝
        if 起 >= 止:
            return 序列.copy(), True

        # 左闭右开：保留前段 + 保留后段
        新序列 = 序列[:起] + 序列[止:]

        return 新序列, True

    except Exception:
        return [], False