import json


def 遍历_值_取键名(数据对象, 目标值):
    """
    查找 JSON 对象中所有等于指定值的键名。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标值 (Any): 要查找的值。

    Returns:
        list[str]: 所有匹配目标值的键名列表。
            如果没有匹配或发生异常，则返回空列表。

    Example:
        数据 = {
            "产品价格": 20.54,
            "库存": [20.54, {"批次": [1, 2, {"产品价格": 20.54}]}],
            "详情": {"重量": 20.54, "规格": {"数值": 10}}
        }
        结果 = 遍历_值_取键名(数据, 20.54)
        print(结果)
        # ["产品价格", "产品价格", "重量"]
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        匹配键列表 = []

        def _递归查找键名(节点):
            """内部递归函数：遍历节点并记录匹配值的键名。"""
            if isinstance(节点, dict):
                for k, v in 节点.items():
                    if v == 目标值:
                        匹配键列表.append(k)
                    if isinstance(v, (dict, list)):
                        _递归查找键名(v)
            elif isinstance(节点, list):
                for el in 节点:
                    if isinstance(el, (dict, list)):
                        _递归查找键名(el)

        _递归查找键名(数据对象)
        return 匹配键列表

    except Exception:
        return []