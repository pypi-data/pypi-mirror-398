import json
import re
from typing import Any, List, Union


def 文本数据查找_保留键(
    数据对象: Union[dict, list, str, bytes],
    层级路径: str,
    键: str,
    值: Any,
    保留键列表: List[str] | None = None,
    *,
    自动类型识别: bool = True,
) -> List[dict]:
    """在指定层级路径下查找满足“键==值”的字典，可选择性保留指定字段。

    本实现不依赖 jsonpath，支持路径语法：
        - 点式层级：a.b.c
        - 通配层级：*（匹配当前层所有键或所有列表元素）
        - 列表索引：edges[0] / edges[*]
        - 组合示例：data.第一层.edges[*].第二层

    功能说明：
        这是 `文本数据查找` 的增强版。

        1. 先利用旧函数找到所有匹配字典。
        2. 若 `保留键列表` 为 None 或 空列表：
               → 返回“整个字典”，不做任何字段过滤。
        3. 若 `保留键列表` 非空：
               → 只保留列表中存在的键，形成更精简的结构。

    Args:
        数据对象: dict/list/JSON 字符串/bytes。
        层级路径: 与老函数一致，例如 "data.第一层.第二层"。
        键: 匹配的键名。
        值: 匹配的目标值。
        保留键列表: 需要保留的键名列表；为空则保留全部字段。
        自动类型识别: 同 `文本数据查找`。

    Returns:
        list[dict]: 匹配后的字典列表（可能是全量，也可能是过滤后的）。
    """
    try:
        # 用旧函数拿到完整结果
        原始结果 = 文本数据查找(
            数据对象=数据对象,
            层级路径=层级路径,
            键=键,
            值=值,
            自动类型识别=自动类型识别,
        )

        # 情况 1：保留键列表为空 → 保持原样
        if not 保留键列表:
            return 原始结果

        # 情况 2：正常过滤
        if not isinstance(保留键列表, (list, tuple, set)):
            return []  # 输入不合法的兜底策略

        保留键列表 = [str(k) for k in 保留键列表]

        精简结果: List[dict] = []
        for 项 in 原始结果:
            if not isinstance(项, dict):
                continue
            子字典 = {k: 项[k] for k in 保留键列表 if k in 项}
            精简结果.append(子字典)

        return 精简结果
    except Exception:
        # 任何异常：绝对不往外抛，直接返回空列表
        return []


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
    """
    try:
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
                # 类型转换失败就保持原始字符串
                pass

        起点列表 = _按路径取节点们(数据对象, 层级路径)

        结果: List[dict] = []
        for 节点 in 起点列表:
            _递归收集匹配字典(节点, 键, 值, 结果)
        return 结果
    except Exception:
        # 任何异常：绝对不往外抛，直接返回空列表
        return []


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
