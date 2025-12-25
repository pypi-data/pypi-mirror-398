import json
import re
from typing import Any, List, Union, Iterable, Optional, Dict


def 数值数据查找(
        数据对象: Union[Dict[str, Any], List[Any], str, bytes, bytearray],
        层级路径: str,
        键: str,
        运算符: str,
        值: Union[int, float, str],
        *,
        自动类型识别: bool = True,
) -> List[dict]:
    """在给定层级路径下递归查找，返回满足“键 运算符 值”的字典层级。

    设计要点：
    - 路径只限定**起点**：从命中的节点开始向下递归匹配。
    - 支持路径通配：`*`、`[数字]`、`[*]`，例如 `data.名单[*]`、`core2.products[*]`。
    - “数值比较”优先：会尽量把双方转成数字后比较；`==`/`!=` 失败时回退到原样比较。
    - 键可写成**点式子路径**（如 `"stats.score"`），用于在对象内部再次下钻。

    Args:
        数据对象: dict/list/JSON 字符串/bytes。
        层级路径: 起点路径（如 "data.名单"、"core2.products[*]"），支持 `*` 与 `[索引]/[*]`。
        键: 需要比较的字段名，支持点式子路径（如 "属性.分数"）。
        运算符: 仅支持 "==", "!=", ">", "<", ">=", "<="。
        值: 用于比较的目标值；可传数字或数字字符串。
        自动类型识别: True 时，会把 "10"→10、"3.14"→3.14、"true"/"false"→布尔、"null"/"none"→None。

    Returns:
        list[dict]: 所有满足条件的“所在层级字典”；无匹配返回空列表。

    示例:
        示例数据 = {
            "data": {
                "名单": [
                    {"姓名": "张三", "年龄": 18, "分数": 82.5},
                    {"姓名": "李四", "年龄": 22, "分数": 91},
                    {"姓名": "王五", "年龄": 20, "分数": 75},
                    {"姓名": "赵六", "年龄": 19, "分数": 60}
                ]
            }
        }
        # 查找 年龄 >= 20
        结果 = 数值数据查找(示例数据, "data.名单", "年龄", ">=", 20)
        # 结果: [{'姓名': '李四', '年龄': 22, '分数': 91}, {'姓名': '王五', '年龄': 20, '分数': 75}]
    """
    # 1) 解析 JSON 字符串/bytes
    if isinstance(数据对象, (str, bytes, bytearray)):
        try:
            数据对象 = json.loads(数据对象)
        except Exception:
            return []

    # 2) 运算符校验
    允许 = {"==", "!=", ">", "<", ">=", "<="}
    if 运算符 not in 允许:
        return []

    # 3) 目标值预处理（尽量转为数字；失败保持原值）
    目标值 = _智能解析标量(值) if 自动类型识别 else 值

    # 4) 获取起点节点们
    起点列表 = _按路径取节点们(数据对象, 层级路径)

    # 5) 从每个起点向下递归，匹配“所在层级字典”
    输出: List[dict] = []
    for 节点 in 起点列表:
        _递归匹配_数值比较(节点, 键.split("."), 运算符, 目标值, 输出, 自动类型识别)
    return 输出


# ----------------- 内部工具函数 -----------------

_SEG_RE = re.compile(r"^(?P<name>[^.\[\]]+|\*)(?:\[(?P<idx>\*|\d+)\])?$")


def _按路径取节点们(root: Any, 路径: str) -> List[Any]:
    if not 路径:
        return [root]
    段们 = 路径.split(".")
    当前: List[Any] = [root]
    for 段 in 段们:
        m = _SEG_RE.match(段.strip())
        if not m:
            return []
        名, 索引 = m.group("name"), m.group("idx")

        下一: List[Any] = []
        for 节点 in 当前:
            if isinstance(节点, dict):
                值们 = list(节点.values()) if 名 == "*" else [节点.get(名)]
                for v in 值们:
                    _推进一层(v, 索引, 下一)
            elif isinstance(节点, list):
                if 名 == "*":
                    for el in 节点:
                        _推进一层(el, 索引, 下一)
                else:
                    for el in 节点:
                        if isinstance(el, dict):
                            _推进一层(el.get(名), 索引, 下一)
        当前 = [x for x in 下一 if x is not None]
        if not 当前:
            return []
    return 当前


def _推进一层(值: Any, 索引: Optional[str], 收集: List[Any]) -> None:
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


def _递归匹配_数值比较(
        节点: Any,
        键路径: List[str],
        运算符: str,
        目标值: Any,
        输出: List[dict],
        自动类型识别: bool,
) -> None:
    """DFS：遇到 dict 就尝试取值并比较；无论是否命中都继续向下。"""
    if isinstance(节点, dict):
        # 取出候选值（支持键的子路径 a.b.c）
        候选值 = _取值_按键路径(节点, 键路径)
        if 候选值 is not None:
            if _满足比较(候选值, 运算符, 目标值, 自动类型识别):
                输出.append(节点)
        # 继续向下
        for v in 节点.values():
            _递归匹配_数值比较(v, 键路径, 运算符, 目标值, 输出, 自动类型识别)
    elif isinstance(节点, list):
        for el in 节点:
            _递归匹配_数值比较(el, 键路径, 运算符, 目标值, 输出, 自动类型识别)


def _取值_按键路径(对象: Any, 键路径: List[str]) -> Any:
    节点 = 对象
    for 段 in 键路径:
        if isinstance(节点, dict):
            节点 = 节点.get(段)
        else:
            return None
        if 节点 is None:
            return None
    return 节点


def _智能解析标量(x: Any) -> Any:
    """把字符串形式的数字/布尔/null 转成对应类型；其他保持原值。"""
    if not isinstance(x, str):
        return x
    s = x.strip()
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none"):
        return None
    # 整数 / 浮点数
    try:
        if re.fullmatch(r"[+-]?\d+", s):
            return int(s)
        return float(s)
    except Exception:
        return x


def _满足比较(候选: Any, 运算符: str, 目标值: Any, 自动类型识别: bool) -> bool:
    """优先做数值比较；==/!= 失败时回退到原样比较。"""
    # 预处理候选值
    原候选 = 候选
    if 自动类型识别:
        候选 = _智能解析标量(候选)

    # 尝试数值比较
    if isinstance(候选, (int, float)) and isinstance(目标值, (int, float)):
        if 运算符 == "==":
            return 候选 == 目标值
        if 运算符 == "!=":
            return 候选 != 目标值
        if 运算符 == ">":
            return 候选 > 目标值
        if 运算符 == "<":
            return 候选 < 目标值
        if 运算符 == ">=":
            return 候选 >= 目标值
        if 运算符 == "<=":
            return 候选 <= 目标值
        return False

    # 非数值：仅支持 == / !=（其余返回 False）
    if 运算符 == "==":
        return 原候选 == 目标值
    if 运算符 == "!=":
        return 原候选 != 目标值
    return False
