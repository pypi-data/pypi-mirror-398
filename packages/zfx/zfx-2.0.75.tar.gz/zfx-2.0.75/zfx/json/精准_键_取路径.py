import json
import re


def 精准_键_取路径(数据对象, 父路径, 目标键):
    """
    功能：
        在指定的父路径下（可含通配符 * 与索引 [n]/[*]）递归查找所有名为“目标键”的键，
        返回每个命中键的完整 JSON 路径（形如 $['a'][0]['b']）。

    参数:
        - 数据对象 (dict 或 str): Python 字典对象或 JSON 字符串。
        - 父路径 (str): 起点路径。支持：
            1) 点分层级：a.b.c
            2) 通配名：*
            3) 列表索引：[0] 或 [*]
            例如 "*.address.[0].details"
            说明：父路径可为空串 ""，表示从根开始，等价于 "$"。
        - 目标键 (str): 需要匹配的键名。

    返回:
        - list: 所有命中键的完整路径字符串列表；若无命中或异常，返回空列表。

    示例:
        数据 = {
            "用户": {"姓名": "张三", "地址": {"城市": "北京"}},
            "订单": [{"地址": {"城市": "上海"}}]
        }
        结果 = 精准_键_取路径(数据, "*", "城市")
        print(结果)
        # ["$['用户']['地址']['城市']", "$['订单'][0]['地址']['城市']"]
    """
    try:
        # 1) 兼容 JSON 字符串
        if isinstance(数据对象, str):
            数据对象 = json.loads(数据对象)

        # 2) 解析父路径，找到起点节点们（每个元素是 (节点值, 路径片段列表)）
        起点列表 = _按父路径取起点(数据对象, 父路径)

        # 3) 从每个起点向下 DFS，收集所有“目标键”的路径
        结果路径 = []
        for 节点值, 路径片段 in 起点列表:
            _深搜_收集键路径(节点值, 路径片段, 目标键, 结果路径)

        return 结果路径
    except Exception:
        return []


# ==============================
# 内部工具：父路径解析与推进
# ==============================

_段正则 = re.compile(r'^(?P<name>[^.\[\]]+|\*)(?:\[(?P<idx>\*|\d+)\])?$')

def _按父路径取起点(root, 父路径):
    """
    输入根对象和父路径，返回所有命中的起点节点：
    列表元素为 (节点值, 路径片段列表)，路径片段用于后续格式化为 $[...] 形式。
    """
    if not 父路径 or 父路径 == "$":
        return [(root, [])]

    段们 = 父路径.split(".")
    当前层 = [(root, [])]  # (值, 路径片段列表)

    for 段 in 段们:
        段 = 段.strip()
        if not 段:
            return []
        m = _段正则.match(段)
        if not m:
            return []

        名称 = m.group("name")
        索引 = m.group("idx")
        下一层 = []

        for 值, 片段 in 当前层:
            if isinstance(值, dict):
                if 名称 == "*":
                    # 遍历所有键
                    for k, v in 值.items():
                        _推进一层(v, 片段 + [("key", k)], 索引, 下一层)
                else:
                    v = 值.get(名称, None)
                    if v is not None:
                        _推进一层(v, 片段 + [("key", 名称)], 索引, 下一层)

            elif isinstance(值, list):
                if 名称 == "*":
                    # 遍历列表每个元素
                    for i, el in enumerate(值):
                        _推进一层(el, 片段 + [("index", i)], 索引, 下一层)
                else:
                    # 名称命中：仅当元素是 dict 时取该键
                    for i, el in enumerate(值):
                        if isinstance(el, dict) and 名称 in el:
                            _推进一层(el[名称], 片段 + [("index", i), ("key", 名称)], 索引, 下一层)

        当前层 = 下一层
        if not 当前层:
            return []

    return 当前层


def _推进一层(值, 片段, 索引, 收集列表):
    """
    根据索引语义把 (值, 片段) 推进到下一层：
      - 无索引：直接加入
      - [*]：若值为 list，则展开每个元素
      - [n]：若值为 list，则取第 n 个
    """
    if 索引 is None:
        收集列表.append((值, 片段))
        return

    # 需要列表索引
    if not isinstance(值, list):
        return

    if 索引 == "*":
        for i, el in enumerate(值):
            收集列表.append((el, 片段 + [("index", i)]))
    else:
        i = int(索引)
        if 0 <= i < len(值):
            收集列表.append((值[i], 片段 + [("index", i)]))


# ==============================
# 内部工具：DFS 收集键路径
# ==============================

def _深搜_收集键路径(节点值, 路径片段, 目标键, 结果路径列表):
    """
    在节点值下递归搜索所有名为“目标键”的键，并把完整路径写入结果列表。
    """
    if isinstance(节点值, dict):
        # 命中当前层的键
        if 目标键 in 节点值:
            完整片段 = 路径片段 + [("key", 目标键)]
            结果路径列表.append(_片段转路径(完整片段))

        # 继续向下递归
        for k, v in 节点值.items():
            _深搜_收集键路径(v, 路径片段 + [("key", k)], 目标键, 结果路径列表)

    elif isinstance(节点值, list):
        for i, el in enumerate(节点值):
            _深搜_收集键路径(el, 路径片段 + [("index", i)], 目标键, 结果路径列表)


def _片段转路径(片段列表):
    """
    把路径片段列表（("key", 名称)/("index", 下标)）格式化为 $['a'][0]['b'] 字符串。
    """
    parts = ["$"]
    for 种类, 值 in 片段列表:
        if 种类 == "key":
            # 简单转义单引号
            k = str(值).replace("\\", "\\\\").replace("'", "\\'")
            parts.append("['{}']".format(k))
        else:  # index
            parts.append("[{}]".format(值))
    return "".join(parts)
