import json


def 遍历_值_更新(数据对象, 目标值, 新值):
    """
    更新 JSON 对象中所有与目标值相等的项为新值。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标值 (Any): 需要被替换的目标值。
        新值 (Any): 用于替换目标值的新值。

    Returns:
        dict | list: 更新后的 JSON 对象。
            如果发生异常则返回空字典。

    Example:
        数据 = {
            "产品价格": 20.54,
            "库存": [20.54, {"批次": [1, 2, {"产品价格": 20.54}]}],
            "详情": {"重量": 20.54, "规格": {"数值": 10}}
        }
        结果 = 遍历_值_更新(数据, 20.54, 99.99)
        print(结果)
        # {
        #   "产品价格": 99.99,
        #   "库存": [99.99, {"批次": [1, 2, {"产品价格": 99.99}]}],
        #   "详情": {"重量": 99.99, "规格": {"数值": 10}}
        # }
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        def _递归更新值(节点):
            """内部递归函数：遍历节点并替换匹配值。"""
            if isinstance(节点, dict):
                for k, v in 节点.items():
                    if v == 目标值:
                        节点[k] = 新值
                    elif isinstance(v, (dict, list)):
                        _递归更新值(v)
            elif isinstance(节点, list):
                for i, v in enumerate(节点):
                    if v == 目标值:
                        节点[i] = 新值
                    elif isinstance(v, (dict, list)):
                        _递归更新值(v)

        _递归更新值(数据对象)
        return 数据对象

    except Exception:
        return {}
