import json


def 遍历_键_删除(数据对象, 目标键):
    """
    删除 JSON 对象中所有指定的键。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标键 (str): 需要删除的键名。

    Returns:
        dict | list: 删除指定键后的 JSON 对象。
            如果发生异常则返回空字典。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "密码": "12345"},
            "订单": [{"编号": "A001", "密码": "abc"}, {"编号": "A002"}]
        }
        结果 = 遍历_键_删除(数据, "密码")
        print(结果)
        # {
        #   "用户": {"姓名": "张三"},
        #   "订单": [{"编号": "A001"}, {"编号": "A002"}]
        # }
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        def _递归删除键(节点):
            """内部递归函数：删除当前节点中的目标键并向下递归。"""
            if isinstance(节点, dict):
                if 目标键 in 节点:
                    del 节点[目标键]
                # 注意：删除后仍需继续递归其余值
                for v in list(节点.values()):
                    if isinstance(v, (dict, list)):
                        _递归删除键(v)

            elif isinstance(节点, list):
                for el in 节点:
                    if isinstance(el, (dict, list)):
                        _递归删除键(el)

        _递归删除键(数据对象)
        return 数据对象

    except Exception:
        return {}
