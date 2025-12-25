import json


def 遍历_键_取路径(数据对象, 目标键):
    """
    查找 JSON 对象中所有指定键的完整路径。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标键 (str): 要查找的键名。

    Returns:
        list[str]: 所有匹配键的 JSON 路径列表。
            如果没有匹配或发生异常，则返回空列表。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [
                {"编号": "A001", "地址": {"城市": "上海"}},
                {"编号": "A002", "地址": {"城市": "广州"}}
            ]
        }
        结果 = 遍历_键_取路径(数据, "城市")
        print(结果)
        # ["$['用户']['地址']['城市']", "$['订单'][0]['地址']['城市']", "$['订单'][1]['地址']['城市']"]
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        路径结果 = []

        def _递归查找(节点, 路径片段):
            """内部递归函数：遍历节点，记录目标键路径。"""
            if isinstance(节点, dict):
                for k, v in 节点.items():
                    新片段 = 路径片段 + [("key", k)]
                    if k == 目标键:
                        路径结果.append(_片段转路径(新片段))
                    if isinstance(v, (dict, list)):
                        _递归查找(v, 新片段)
            elif isinstance(节点, list):
                for i, el in enumerate(节点):
                    新片段 = 路径片段 + [("index", i)]
                    if isinstance(el, (dict, list)):
                        _递归查找(el, 新片段)

        def _片段转路径(片段列表):
            """把路径片段转为 JSONPath 风格字符串。"""
            parts = ["$"]
            for 种类, 值 in 片段列表:
                if 种类 == "key":
                    k = str(值).replace("\\", "\\\\").replace("'", "\\'")
                    parts.append(f"['{k}']")
                else:
                    parts.append(f"[{值}]")
            return "".join(parts)

        _递归查找(数据对象, [])
        return 路径结果

    except Exception:
        return []
