import json


def 遍历_键_取值(数据对象, 目标键):
    """
    查找 JSON 对象中所有指定键的值。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标键 (str): 需要查找的键名。

    Returns:
        list[Any]: 所有匹配目标键的值组成的列表。
            如果没有匹配或发生异常，则返回空列表。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [
                {"编号": "A001", "地址": {"城市": "上海"}},
                {"编号": "A002", "地址": {"城市": "广州"}}
            ]
        }
        结果 = 遍历_键_取值(数据, "城市")
        print(结果)
        # ["北京", "上海", "广州"]
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        匹配值列表 = []

        def _递归取值(节点):
            """内部递归函数：遍历节点并收集目标键的值。"""
            if isinstance(节点, dict):
                for k, v in 节点.items():
                    if k == 目标键:
                        匹配值列表.append(v)
                    if isinstance(v, (dict, list)):
                        _递归取值(v)
            elif isinstance(节点, list):
                for el in 节点:
                    if isinstance(el, (dict, list)):
                        _递归取值(el)

        _递归取值(数据对象)
        return 匹配值列表

    except Exception:
        return []
