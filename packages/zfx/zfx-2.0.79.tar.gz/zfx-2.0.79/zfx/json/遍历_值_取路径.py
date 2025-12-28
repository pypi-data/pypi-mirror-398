import json


def 遍历_值_取路径(数据对象, 目标值):
    """
    查找 JSON 对象中指定值的所有路径。
    支持任意层级嵌套结构，包括字典与列表。

    Args:
        数据对象 (dict | list | str): Python 字典、列表或 JSON 字符串。
        目标值 (Any): 要查找的值。数字直接写数字，字符串需加引号。

    Returns:
        list[str]: 匹配到的所有值的 JSON 路径列表。
            如果没有匹配或发生异常，则返回空列表。

    Example:
        数据 = {
            "产品价格": 20.54,
            "库存": [20.54, 15, 20.54],
            "详情": {
                "重量": 20.54,
                "规格": {"数值": 10}
            }
        }
        结果 = 遍历_值_取路径(数据, 20.54)
        print(结果)
        # ["$['产品价格']", "$['库存'][0]", "$['库存'][2]", "$['详情']['重量']"]
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        匹配路径列表 = []

        def _递归查找(节点, 路径片段):
            """内部递归函数，用于遍历节点并记录目标值路径。"""
            if 节点 == 目标值:
                匹配路径列表.append(_片段转路径(路径片段))
                return

            if isinstance(节点, dict):
                for k, v in 节点.items():
                    _递归查找(v, 路径片段 + [("key", k)])

            elif isinstance(节点, list):
                for i, el in enumerate(节点):
                    _递归查找(el, 路径片段 + [("index", i)])

        _递归查找(数据对象, [])
        return 匹配路径列表

    except Exception:
        return []


def _片段转路径(片段列表):
    """
    将路径片段转换为标准 JSONPath 表示形式。
    例如 [("key", "产品价格"), ("index", 0)] -> "$['产品价格'][0]"

    Args:
        片段列表 (list[tuple[str, Any]]): 路径片段。
    Returns:
        str: 转换后的路径字符串。
    """
    parts = ["$"]
    for 种类, 值 in 片段列表:
        if 种类 == "key":
            k = str(值).replace("\\", "\\\\").replace("'", "\\'")
            parts.append(f"['{k}']")
        else:
            parts.append(f"[{值}]")
    return "".join(parts)