from __future__ import annotations

from typing import Any, List, Set


def 提取值为字典_不递归(
    数据: Any,
    *,
    去重: bool = True,
) -> List[dict]:
    """从嵌套结构中提取所有“字典中 value 为 dict”的值，并且命中后不递归该 dict 内部。

    功能说明:
        - 遍历规则（核心语义）：
            1) 遇到 dict：
               - 遍历其 values：
                 - 若 value 是 dict：收集该 dict，并停止对该 dict 的递归（不进入该 dict 内部）。
                 - 若 value 是 list：把 list 当作“容器”继续遍历其元素（仅递归元素中的 dict / list）。
                 - 其他类型忽略。
            2) 遇到 list：
               - 把 list 当作“容器”遍历其元素：
                 - 元素为 dict / list：继续递归。
                 - 其他类型忽略。

        - 结果：
            返回所有命中的 dict（保持发现顺序）。

    Args:
        数据 (Any): 任意嵌套数据结构，常见为 dict / list（也可能是其它类型，都会安全处理）。
        去重 (bool):
            - True: 按对象 id 去重（同一个 dict 对象被多处引用时只返回一次）。
            - False: 不去重，命中几次返回几次。

    Returns:
        List[dict]:
            - 返回命中的所有 dict。
            - 若无命中或输入不含可遍历结构，返回空列表。

    Notes:
        - “不递归”仅针对“命中的 dict 值本身”：
          一旦某个 value 是 dict，被收集后不会再进入该 dict 内部继续扫描。
        - 函数不修改输入数据结构，不输出日志，不抛出异常，适合作为底层通用工具函数。
    """
    结果: List[dict] = []
    已收集ID: Set[int] = set()

    def 收集(目标: dict) -> None:
        if not 去重:
            结果.append(目标)
            return

        目标ID = id(目标)
        if 目标ID not in 已收集ID:
            已收集ID.add(目标ID)
            结果.append(目标)

    def 遍历(节点: Any) -> None:
        try:
            if isinstance(节点, dict):
                for 值 in 节点.values():
                    if isinstance(值, dict):
                        收集(值)
                        # 命中 dict：不递归该 dict 内部
                        continue

                    if isinstance(值, list):
                        # list 作为容器：继续向下找（但命中 dict 值仍不递归）
                        遍历(值)
                        continue

                    # 其他类型忽略

            elif isinstance(节点, list):
                for 元素 in 节点:
                    if isinstance(元素, (dict, list)):
                        遍历(元素)
                    # 其他类型忽略
        except Exception:
            # 底层函数：吞异常，保持稳定
            return

    遍历(数据)
    return 结果