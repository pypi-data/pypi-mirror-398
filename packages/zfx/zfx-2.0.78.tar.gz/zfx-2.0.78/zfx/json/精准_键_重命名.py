import json
import re


def 精准_键_重命名(数据对象, 父路径, 旧键, 新键):
    """
    在指定的父路径下重命名 JSON 对象中的指定键。
    支持父路径包含通配符 `*` 及列表索引 `[n]` / `[*]`。

    Args:
        数据对象 (dict | str): Python 字典对象或 JSON 字符串。
        父路径 (str): 要查找的父路径，可使用 `*`、`[n]`、`[*]`。
            例如 "*.address.[0].details"。
        旧键 (str): 需要被替换的旧键名。
        新键 (str): 新的键名。

    Returns:
        dict: 重命名后的 JSON 对象。
            如果出错则返回空字典。

    Example:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [{"地址": {"城市": "上海"}}]
        }
        结果 = 精准_键_重命名(数据, "*", "城市", "City")
        print(结果)
        # {
        #   "用户": {"姓名": "张三", "地址": {"City": "北京"}},
        #   "订单": [{"地址": {"City": "上海"}}]
        # }
    """
    try:
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        起点们 = _按父路径取起点(数据对象, 父路径)
        for 节点值, _路径 in 起点们:
            _深搜_重命名键(节点值, 旧键, 新键)

        return 数据对象
    except Exception:
        return {}


_段正则 = re.compile(r'^(?P<name>[^.\[\]]+|\*)(?:\[(?P<idx>\*|\d+)\])?$')


def _按父路径取起点(root, 父路径):
    """
    根据父路径提取所有起点节点。

    Args:
        root (dict | list): JSON 根对象。
        父路径 (str): 父路径表达式，支持 `*`、`[n]`、`[*]`。

    Returns:
        list[tuple[Any, list[tuple[str, Any]]]]: 每个起点由 `(节点值, 路径片段)` 组成。
    """
    if not 父路径 or 父路径 == "$":
        return [(root, [])]

    段们 = 父路径.split(".")
    当前层 = [(root, [])]

    for 段 in 段们:
        段 = 段.strip()
        m = _段正则.match(段)
        if not m:
            return []
        名称 = m.group("name")
        索引 = m.group("idx")
        下一层 = []

        for 值, 片段 in 当前层:
            if isinstance(值, dict):
                if 名称 == "*":
                    for k, v in 值.items():
                        _推进一层(v, 片段 + [("key", k)], 索引, 下一层)
                elif 名称 in 值:
                    _推进一层(值[名称], 片段 + [("key", 名称)], 索引, 下一层)

            elif isinstance(值, list):
                if 名称 == "*":
                    for i, el in enumerate(值):
                        _推进一层(el, 片段 + [("index", i)], 索引, 下一层)
                else:
                    for i, el in enumerate(值):
                        if isinstance(el, dict) and 名称 in el:
                            _推进一层(el[名称], 片段 + [("index", i), ("key", 名称)], 索引, 下一层)

        当前层 = 下一层
        if not 当前层:
            return []

    return 当前层


def _推进一层(值, 片段, 索引, 收集列表):
    """
    根据索引或通配规则推进到下一层。

    Args:
        值 (Any): 当前节点的值。
        片段 (list): 路径片段。
        索引 (str | None): `[n]` 或 `[*]`。
        收集列表 (list): 收集结果的列表。
    """
    if 索引 is None:
        收集列表.append((值, 片段))
        return

    if not isinstance(值, list):
        return

    if 索引 == "*":
        for i, el in enumerate(值):
            收集列表.append((el, 片段 + [("index", i)]))
    else:
        i = int(索引)
        if 0 <= i < len(值):
            收集列表.append((值[i], 片段 + [("index", i)]))


def _深搜_重命名键(节点值, 旧键, 新键):
    """
    在节点下递归搜索所有旧键并执行重命名。

    Args:
        节点值 (Any): 当前节点。
        旧键 (str): 要替换的旧键名。
        新键 (str): 新键名。
    """
    if isinstance(节点值, dict):
        if 旧键 in 节点值:
            节点值[新键] = 节点值.pop(旧键)
        for v in 节点值.values():
            _深搜_重命名键(v, 旧键, 新键)
    elif isinstance(节点值, list):
        for el in 节点值:
            _深搜_重命名键(el, 旧键, 新键)
