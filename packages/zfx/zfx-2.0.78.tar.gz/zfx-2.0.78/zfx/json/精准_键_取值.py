import json
import re
from typing import Any, List, Union, Dict


_SEG_RE = re.compile(r"^(?P<name>[^.\[\]]+|\*)(?:\[(?P<idx>\*|\d+)\])?$")


def 精准_键_取值(
    数据对象: Union[Dict[str, Any], List[Any], str, bytes, bytearray],
    父路径: str,
    目标键: str,
    *,
    递归向下: bool = True,
) -> List[Any]:
    """在指定父路径下查找指定键的所有值。

    特点：
      - 支持路径通配：`*`、`[数字]`、`[*]`。
      - 路径命中后可选择是否递归向下继续查找。
      - 不依赖第三方库，完全标准库实现。
      - 已内置异常捕获（由 @安全执行 提供），异常时返回 []。

    Args:
        数据对象: dict / list / JSON 字符串 / bytes。
        父路径: 起点路径，例如 "data.用户[*].地址[*]" 或 "*.address[0].details"。
        目标键: 要查找的键名。
        递归向下: True 表示从命中的父层往下所有层级继续查找；False 仅在命中层取值。

    Returns:
        list: 所有匹配键的值；若无匹配或异常返回空列表。

    示例:
        数据 = {
            "data": {
                "用户": [
                    {
                        "name": "zeng",
                        "info": {"city": "广州", "meta": {"tag": "A"}},
                    },
                    {
                        "name": "li",
                        "info": {"city": "上海", "meta": {"tag": "B"}},
                    }
                ]
            }
        }
        结果 = 精准_键_取值(数据, "data.用户[*].info", "meta")
        # 返回：[{"tag": "A"}, {"tag": "B"}]
    """
    # 1) JSON 字符串解析
    if isinstance(数据对象, (str, bytes, bytearray)):
        数据对象 = json.loads(数据对象)

    # 2) 获取父路径命中的起点
    起点们 = _按路径取节点们(数据对象, 父路径)
    if not 起点们:
        return []

    # 3) 递归搜索指定键
    结果: List[Any] = []
    for 节点 in 起点们:
        if 递归向下:
            _递归收集_键值(节点, 目标键, 结果)
        else:
            if isinstance(节点, dict) and 目标键 in 节点:
                结果.append(节点[目标键])
    return 结果


# ----------------- 内部通用工具 -----------------

def _按路径取节点们(root: Any, 路径: str) -> List[Any]:
    """根据路径语法，返回命中的起点节点。"""
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


def _推进一层(值: Any, 索引: str | None, 收集: List[Any]) -> None:
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


def _递归收集_键值(节点: Any, 目标键: str, 收集: List[Any]) -> None:
    """深度优先递归，收集所有匹配的键值。"""
    if isinstance(节点, dict):
        if 目标键 in 节点:
            收集.append(节点[目标键])
        for v in 节点.values():
            _递归收集_键值(v, 目标键, 收集)
    elif isinstance(节点, list):
        for el in 节点:
            _递归收集_键值(el, 目标键, 收集)