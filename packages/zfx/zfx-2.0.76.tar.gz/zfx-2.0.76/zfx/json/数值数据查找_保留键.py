import json
import re
from typing import Any, List, Union, Optional, Dict


def 数值数据查找_保留键(
        数据对象: Union[Dict[str, Any], List[Any], str, bytes, bytearray],
        层级路径: str,
        键: str,
        运算符: str,
        值: Union[int, float, str],
        保留键列表: List[str] | None = None,
        *,
        自动类型识别: bool = True,
) -> List[dict]:
    """在嵌套结构中按数值条件筛选字典，并可选择性只保留指定字段。

    功能说明:
        1. 使用 `数值数据查找`:
            - 根据给定的层级路径，从命中的起点向下递归遍历；
            - 找出所有满足「键 运算符 值」条件的字典层级。

        2. 对结果做字段精简:
            - 若 `保留键列表` 为 None 或空列表:
                直接返回完整字典，不做任何字段过滤。
            - 若 `保留键列表` 非空:
                对每个命中字典按键名做一次过滤，只保留列表中的键。

        适合场景:
            - 原始 JSON 每条记录字段很多，只关心部分字段，例如价格、货币代码、国家代码等。
            - 希望在查询阶段就“瘦身”结果，减轻后续处理/落库压力。

        路径语法(与 `数值数据查找` 完全一致):
            - 点式层级: data.名单、core2.products
            - 通配符:
                *            匹配当前层所有键或列表元素
                a[*]         匹配列表 a 的所有元素
                a[0]         匹配列表 a 的第 0 个元素
            - 组合示例:
                data.名单[*]
                core2.products[*]
                data.第一层.第二层[*].明细

        比较规则:
            - 支持运算符: "==", "!=", ">", "<", ">=", "<="
            - 当 `自动类型识别=True` 时:
                会尝试把字符串转换为数字/布尔/None，例如:
                    "10"      → 10
                    "3.14"    → 3.14
                    "true"    → True
                    "false"   → False
                    "null"    → None
            - 若候选值和目标值均为数值类型(int/float)，则执行数值比较。
            - 否则:
                仅对 "==" / "!=" 使用原始值做相等/不等比较，
                其他比较运算一律返回 False。

        异常处理:
            - 本函数内部对整体流程做了 try/except 包裹。
            - 任意步骤出现异常(路径异常、类型异常等)，都会返回空列表 []，
              不会向外抛出异常，以避免影响调用方业务流程。

    Args:
        数据对象: 原始数据，可以是字典、列表、JSON 字符串或 bytes。
        层级路径: 起点路径，如 "data.名单"、"core2.products[*]"，支持 * 与 [索引]/[*]。
        键: 需要比较的字段名，支持点式子路径(如 "属性.分数")，用于在字典内部继续下钻。
        运算符: 比较运算符，仅支持 "==", "!=", ">", "<", ">=", "<="。
        值: 用于比较的目标值，可为数字或数字字符串。
        保留键列表: 需要保留的键名列表;
                  为 None 或 [] 时不做过滤，返回完整字典。
        自动类型识别: 为 True 时启用智能类型解析(数字/布尔/None)，
                    逻辑与 `数值数据查找` 中一致。

    Returns:
        list[dict]: 过滤后的字典列表。
            - 正常情况下: 返回满足条件的字典(可能是完整字典，也可能是只保留了部分键)。
            - 无匹配或发生异常时: 返回空列表 []。

    示例:
        示例数据 = {
            "data": {
                "名单": [
                    {"姓名": "张三", "年龄": 18, "分数": 82.5, "国家": "CN"},
                    {"姓名": "李四", "年龄": 22, "分数": 91,   "国家": "US"},
                    {"姓名": "王五", "年龄": 20, "分数": 75,   "国家": "JP"}
                ]
            }
        }

        # 示例 1: 查找年龄 >= 20，保留完整字典
        结果1 = 数值数据查找_保留键(
            示例数据,
            "data.名单",
            "年龄",
            ">=",
            20,
            保留键列表=None,
        )

        # 示例 2: 查找年龄 >= 20，仅保留姓名和分数
        结果2 = 数值数据查找_保留键(
            示例数据,
            "data.名单",
            "年龄",
            ">=",
            20,
            保留键列表=["姓名", "分数"],
        )
    """
    try:
        # 先调用老函数，拿到“完整命中字典列表”
        原始结果 = 数值数据查找(
            数据对象=数据对象,
            层级路径=层级路径,
            键=键,
            运算符=运算符,
            值=值,
            自动类型识别=自动类型识别,
        )

        # 情况 1：保留键列表为空或 None → 保持原样返回
        if not 保留键列表:
            return 原始结果

        # 情况 2：需要做字段过滤
        if not isinstance(保留键列表, (list, tuple, set)):
            return []  # 非法输入，直接兜底空列表

        保留键列表 = [str(k) for k in 保留键列表]

        精简结果: List[dict] = []
        for 项 in 原始结果:
            if not isinstance(项, dict):
                continue
            子字典 = {k: 项[k] for k in 保留键列表 if k in 项}
            精简结果.append(子字典)

        return 精简结果
    except Exception:
        # 升级版同样遵守“不往外抛异常”的原则
        return []


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

    功能定位:
        这是数值比较逻辑的基础实现，更偏向“内部使用”。
        对于业务代码，建议直接调用外层的 `数值数据查找_保留键`，
        仅在需要拿到完整字典且不做字段过滤时，才考虑直接使用本函数。

    设计要点:
        - 路径只限定“起点”:
            从命中的节点开始，向下递归遍历整个子树。
        - 支持路径通配:
            *       匹配当前层所有键或所有列表元素
            a[0]    匹配键 a 对应列表的第 0 个元素
            a[*]    匹配键 a 对应列表的所有元素
        - 数值比较优先:
            在可能的情况下尝试把双方都转成数字后比较。
            当无法做数值比较时，对 "==" 和 "!=" 回退到原始值比较。
        - 键支持点式子路径:
            例如 "stats.score" 或 "属性.分数"，在字典内部继续下钻。

    Args:
        数据对象: dict/list/JSON 字符串/bytes。
        层级路径: 起点路径(如 "data.名单"、"core2.products[*]")，支持 * 与 [索引]/[*]。
        键: 需要比较的字段名，支持点式子路径(如 "属性.分数")。
        运算符: 仅支持 "==", "!=", ">", "<", ">=", "<="。
        值: 用于比较的目标值，可传数字或数字字符串。
        自动类型识别:
            为 True 时，会尝试将字符串转换为:
                - 整数 / 浮点数
                - 布尔值: "true"/"false"
                - None:   "null"/"none"

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
        结果 = 数值数据查找(
            示例数据,
            "data.名单",
            "年龄",
            ">=",
            20,
        )
        # 结果: [{'姓名': '李四', '年龄': 22, '分数': 91},
        #       {'姓名': '王五', '年龄': 20, '分数': 75}]
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