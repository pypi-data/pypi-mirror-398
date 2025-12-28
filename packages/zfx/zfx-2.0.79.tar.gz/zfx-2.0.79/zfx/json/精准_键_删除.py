import json
import re
from typing import Any, List, Union, Optional, Dict

# 路径分段解析：支持 a.b[*].c、a[*]、a[0]、*、*.x 等
_SEG_RE = re.compile(r"^(?P<name>[^.\[\]]+|\*)(?:\[(?P<idx>\*|\d+)\])?$")


def 精准_键_删除(
    数据对象: Union[Dict[str, Any], List[Any], str, bytes, bytearray],
    父路径: str,
    目标键: str,
    *,
    递归向下: bool = True,
    删除所有出现: bool = True,
) -> Union[Dict[str, Any], List[Any]]:
    """在指定父路径下删除指定键（默认递归向下，删除所有出现的该键）。

    设计要点
    - **父路径只限定“起点”**：从该路径命中的节点向下遍历。
    - 支持模糊路径：`*`、`[数字]`、`[*]`，例如：`data.名单[*]`、`core2.products[*]`、`*.address[0]`。
    - 默认会在起点之下的所有层级中**递归删除** `目标键`，可通过参数调整行为。

    Args:
        数据对象: dict/list/JSON 字符串/bytes。若为字符串/bytes，将先 `json.loads`。
        父路径: 起点路径（如 "data.第一层"、"*.address[0].details"、"core2.products[*]"）。
        目标键: 要删除的键名（只对 dict 有效）。
        递归向下: True 表示从起点开始向下所有层级递归删除；False 仅在“起点本身”尝试删除一次。
        删除所有出现: True 表示删除遇到的**所有**同名键；False 表示每个起点仅删**第一次出现**后停止。

    Returns:
        dict | list: 删除后的数据对象；解析/处理失败时返回空 dict `{}`。

    示例:
        数据 = {
            "data": {
                "列表": [
                    {"name": "zeng", "age": 18, "meta": {"tag": "A", "desc": "x"}},
                    {"name": "li", "age": 20, "meta": {"tag": "B", "desc": "y"}}
                ],
                "info": {"meta": {"tag": "C", "desc": "z"}}
            }
        }
        # 在 data 下，递归删除所有层级里的 "meta"
        结果 = 精准_键_删除(数据, "data", "meta")
        # 结果中所有 "meta" 键都被移除
    """
    try:
        # 1) 统一成 Python 对象
        if isinstance(数据对象, (str, bytes, bytearray)):
            数据对象 = json.loads(数据对象)

        # 2) 找到父路径命中的“起点节点们”
        起点们 = _按路径取节点们(数据对象, 父路径)

        # 3) 对每个起点执行删除
        for 起点 in 起点们:
            if 递归向下:
                _递归删除键(起点, 目标键, 删除所有出现)
            else:
                if isinstance(起点, dict) and 目标键 in 起点:
                    del 起点[目标键]

        return 数据对象
    except Exception:
        return {}


# ----------------- 内部工具函数 -----------------

def _按路径取节点们(root: Any, 路径: str) -> List[Any]:
    """根据自定义路径语法，返回一组“起点节点”。"""
    if not 路径 or 路径 == "$":
        return [root]
    段们 = 路径.split(".")
    当前层: List[Any] = [root]
    for 段 in 段们:
        m = _SEG_RE.match(段.strip())
        if not m:
            return []
        名, 索引 = m.group("name"), m.group("idx")

        下一层: List[Any] = []
        for 节点 in 当前层:
            if isinstance(节点, dict):
                值们 = list(节点.values()) if 名 == "*" else [节点.get(名)]
                for v in 值们:
                    _推进一层(v, 索引, 下一层)
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


def _推进一层(值: Any, 索引: Optional[str], 收集: List[Any]) -> None:
    """处理 [idx]/[*] 选择器，推进到下一层。"""
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


def _递归删除键(节点: Any, 目标键: str, 删除所有出现: bool) -> bool:
    """深度优先：在节点下递归删除 目标键。
    返回值：是否在本起点下至少删除过一次（用于 删除所有出现=False 时早停）。
    """
    已删 = False
    if isinstance(节点, dict):
        if 目标键 in 节点:
            del 节点[目标键]
            已删 = True
            if not 删除所有出现:
                return True  # 删一次就结束（针对当前起点）
        # 继续向下
        for k in list(节点.keys()):
            子 = 节点.get(k)
            if _递归删除键(子, 目标键, 删除所有出现):
                已删 = True
                if not 删除所有出现:
                    return True
    elif isinstance(节点, list):
        for el in 节点:
            if _递归删除键(el, 目标键, 删除所有出现):
                已删 = True
                if not 删除所有出现:
                    return True
    return 已删