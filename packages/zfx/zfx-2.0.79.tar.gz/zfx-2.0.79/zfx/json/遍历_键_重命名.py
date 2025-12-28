import json


def 遍历_键_重命名(数据对象, 旧键, 新键):
    """
    重命名 JSON 对象中所有指定的键。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        旧键 (str): 需要被替换的旧键名。
        新键 (str): 替换后的新键名。

    Returns:
        dict | list: 重命名后的 JSON 对象。
            如果发生异常则返回空字典。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [
                {"编号": "A001", "地址": {"城市": "上海"}},
                {"编号": "A002", "地址": {"城市": "广州"}}
            ]
        }
        结果 = 遍历_键_重命名(数据, "地址", "Address")
        print(结果)
        # {
        #   "用户": {"姓名": "张三", "Address": {"城市": "北京"}},
        #   "订单": [
        #       {"编号": "A001", "Address": {"城市": "上海"}},
        #       {"编号": "A002", "Address": {"城市": "广州"}}
        #   ]
        # }
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        def _递归重命名键(节点):
            """内部递归函数：在节点下查找并重命名目标键。"""
            if isinstance(节点, dict):
                # 先处理当前层
                if 旧键 in 节点:
                    节点[新键] = 节点.pop(旧键)
                # 再递归子结构
                for v in list(节点.values()):
                    if isinstance(v, (dict, list)):
                        _递归重命名键(v)
            elif isinstance(节点, list):
                for el in 节点:
                    if isinstance(el, (dict, list)):
                        _递归重命名键(el)

        _递归重命名键(数据对象)
        return 数据对象

    except Exception:
        return {}
