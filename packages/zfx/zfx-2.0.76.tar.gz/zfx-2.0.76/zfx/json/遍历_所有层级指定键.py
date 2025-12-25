import json


def 遍历_所有层级指定键(数据对象, 键名):
    """
    遍历 JSON 对象的所有层级，查找并返回指定键名对应的值。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        键名 (str): 需要查找的键名。

    Returns:
        list[Any]: 所有匹配键名对应的值列表。
            如果没有匹配或发生异常，则返回空列表。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [
                {"编号": "A001", "地址": {"城市": "上海"}},
                {"编号": "A002", "地址": {"城市": "广州"}}
            ],
            "附加": {"地址": "南京"}
        }
        结果 = 遍历_所有层级指定键(数据, "地址")
        print(结果)
        # [
        #   {"城市": "北京"},
        #   {"城市": "上海"},
        #   {"城市": "广州"},
        #   "南京"
        # ]
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        匹配值列表 = []

        def _递归查找(节点):
            """内部递归函数：深度遍历所有层级并收集键名匹配的值。"""
            if isinstance(节点, dict):
                for k, v in 节点.items():
                    if k == 键名:
                        匹配值列表.append(v)
                    if isinstance(v, (dict, list)):
                        _递归查找(v)
            elif isinstance(节点, list):
                for el in 节点:
                    if isinstance(el, (dict, list)):
                        _递归查找(el)

        _递归查找(数据对象)
        return 匹配值列表

    except Exception:
        return []
