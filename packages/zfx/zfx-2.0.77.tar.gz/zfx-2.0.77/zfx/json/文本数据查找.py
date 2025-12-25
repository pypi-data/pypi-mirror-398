import json
import re
from typing import Any, List, Union


def 文本数据查找(
    数据对象: Union[dict, list, str, bytes],
    层级路径: str,
    键: str,
    值: Any,
    *,
    自动类型识别: bool = True,
) -> List[dict]:
    """在给定层级路径下递归查找，返回所有满足“键==值”的字典层级。

    本实现不依赖 jsonpath，支持路径语法：
    - 点式层级：a.b.c
    - 通配层级：*（匹配当前层所有键或所有列表元素）
    - 列表索引：edges[0] / edges[*]
    - 组合示例：data.第一层.edges[*].第二层

    路径命中的节点会作为起点，在其下方递归查找所有满足条件的字典并返回。

    Args:
        数据对象: dict/list/JSON 字符串/bytes。
        层级路径: 例如 "data.第一层.第二层"（支持 * 与 [索引]/[*]）。
        键: 需要匹配的键名（仅在字典对象上判断）。
        值: 需要匹配的值；若 `自动类型识别=True` 且是字符串，会尝试转为 int/float/bool/None。
        自动类型识别: 启用后会把 "18"→18、"true"→True、"null"→None 等，以获得更精确的比较。

    Returns:
        list[dict]: 所有满足条件的“所在层级字典”；无匹配时返回空列表。

    示例:
        数据 = {
            "data": {
                "第一层": {
                    "第二层": [
                        {"name": "zeng", "age": 18},
                        {"name": "li", "age": 20}
                    ]
                }
            }
        }
        结果 = json.文本数据查找(数据, "data.第一层.第二层", "name", "zeng")
        # 结果: [{'name': 'zeng', 'age': 18}]

        深数据 = {"root": [{"box": {"name": "zeng"}}, {"box": {"name": "li"}}]}
        结果2 = json.文本数据查找(深数据, "root[*]", "name", "zeng")
        # 结果2: [{'name': 'zeng'}]
    """
    if isinstance(数据对象, (str, bytes, bytearray)):
        try:
            数据对象 = json.loads(数据对象)
        except Exception:
            return []

    if 自动类型识别 and isinstance(值, str):
        _v = 值.strip().lower()
        try:
            if _v in ("true", "false"):
                值 = (_v == "true")
            elif _v in ("null", "none"):
                值 = None
            else:
                值 = int(值) if re.fullmatch(r"[+-]?\d+", 值.strip()) else float(值)
        except Exception:
            pass

    起点列表 = _按路径取节点们(数据对象, 层级路径)

    结果: List[dict] = []
    for 节点 in 起点列表:
        _递归收集匹配字典(节点, 键, 值, 结果)
    return 结果


# ----------------- 内部工具函数 -----------------

import re as _re
from typing import Any as _Any, List as _List

_SEG_RE = _re.compile(r"^(?P<name>[^.\[\]]+|\*)(?:\[(?P<idx>\*|\d+)\])?$")


def _按路径取节点们(root: _Any, 路径: str) -> _List[_Any]:
    if not 路径:
        return [root]
    段们 = 路径.split(".")

    当前层: _List[_Any] = [root]
    for 段 in 段们:
        m = _SEG_RE.match(段.strip())
        if not m:
            return []
        名 = m.group("name")
        索引 = m.group("idx")

        下一层: _List[_Any] = []
        for 节点 in 当前层:
            if isinstance(节点, dict):
                值们 = list(节点.values()) if 名 == "*" else [节点.get(名)]
                for 值 in 值们:
                    _推进一层(值, 索引, 下一层)
            elif isinstance(节点, list):
                if 名 == "*":
                    for el in 节点:
                        _推进一层(el, 索引, 下一层)
                else:
                    for el in 节点:
                        if isinstance(el, dict):
                            _推进一层(el.get(名), 索引, 下一层)
        当前层 = [x for x in 下一层 if x is not None]
        if not 当前层:
            return []
    return 当前层


def _推进一层(值: _Any, 索引: str | None, 收集: _List[_Any]) -> None:
    if 索引 is None:
        收集.append(值)
        return
    if not isinstance(值, list):
        return
    if 索引 == "*":
        收集.extend(值)
        return
    i = int(索引)
    if 0 <= i < len(值):
        收集.append(值[i])


def _递归收集匹配字典(节点: _Any, 键: str, 目标值: _Any, 输出: _List[dict]) -> None:
    if isinstance(节点, dict):
        if 键 in 节点 and 节点.get(键) == 目标值:
            输出.append(节点)
        for v in 节点.values():
            _递归收集匹配字典(v, 键, 目标值, 输出)
    elif isinstance(节点, list):
        for el in 节点:
            _递归收集匹配字典(el, 键, 目标值, 输出)