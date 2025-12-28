import json


def 遍历_值_取出现次数(数据对象, 目标值):
    """
    统计 JSON 对象中指定值的出现次数。
    支持任意深度的嵌套结构，包括字典和列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标值 (Any): 要统计的值。

    Returns:
        int: 目标值在 JSON 对象中出现的次数。
            如果出现异常，返回 0。

    Example:
        数据 = {
            "产品价格": 20.54,
            "库存": [20.54, 15, 20.54],
            "详情": {"重量": 20.54, "规格": {"数值": 10}}
        }

        出现次数 = 遍历_值_取出现次数(数据, 20.54)

        print(f"目标值出现的次数: {出现次数}")
        # 结果: 4
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        def _递归统计(节点):
            """内部递归统计函数。"""
            if 节点 == 目标值:
                return 1

            if isinstance(节点, dict):
                return sum(_递归统计(v) for v in 节点.values())

            if isinstance(节点, list):
                return sum(_递归统计(v) for v in 节点)

            return 0

        return _递归统计(数据对象)
    except Exception:
        return 0
