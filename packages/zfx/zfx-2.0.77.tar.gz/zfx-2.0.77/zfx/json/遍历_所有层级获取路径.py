import json


def 遍历_所有层级获取路径(数据对象, 键名):
    """
    遍历所有层级查找指定键，并返回每个命中键的完整 JSON 路径与对应值。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        键名 (str): 要查找的键名。

    Returns:
        list[tuple[str, Any]]: 形如 [(路径, 值), ...] 的列表；异常或无命中返回 []。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [{"地址": {"城市": "上海"}}, {"地址": {"城市": "广州"}}]
        }
        结果 = 遍历_所有层级获取路径(数据, "城市")
        print(结果)
        # [
        #   ("$['用户']['地址']['城市']", "北京"),
        #   ("$['订单'][0]['地址']['城市']", "上海"),
        #   ("$['订单'][1]['地址']['城市']", "广州")
        # ]
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        结果 = []

        def _递归(节点, 片段):
            if isinstance(节点, dict):
                for k, v in 节点.items():
                    新片段 = 片段 + [("key", k)]
                    if k == 键名:
                        结果.append((_片段转路径(新片段), v))
                    if isinstance(v, (dict, list)):
                        _递归(v, 新片段)

            elif isinstance(节点, list):
                for i, el in enumerate(节点):
                    新片段 = 片段 + [("index", i)]
                    if isinstance(el, (dict, list)):
                        _递归(el, 新片段)

        _递归(数据对象, [])
        return 结果

    except Exception:
        return []


def _片段转路径(片段列表):
    """将片段列表转为标准 JSONPath 风格字符串，如 [("key","a"),("index",0)] → "$['a'][0]"。"""
    parts = ["$"]
    for 种类, 值 in 片段列表:
        if 种类 == "key":
            k = str(值).replace("\\", "\\\\").replace("'", "\\'")
            parts.append(f"['{k}']")
        else:
            parts.append(f"[{值}]")
    return "".join(parts)
