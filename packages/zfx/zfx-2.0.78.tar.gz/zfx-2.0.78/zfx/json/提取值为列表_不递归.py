from __future__ import annotations
from typing import Any, List, Set


def 提取值为列表_不递归(数据: Any) -> List[list]:
    """从嵌套结构中提取“所有字典键对应的值为 list 的项”，且不继续遍历 list 内部。

    功能说明:
        - 递归遍历所有 dict 层级，收集所有 value 是 list 的值。
        - 命中 list 后，将该 list 作为结果收集，并视为“叶子节点”，不会继续遍历该 list 内部。
        - 若遇到 list 作为“容器”（比如最外层就是 list），会遍历 list 内的元素：
            - 仅当元素是 dict 才会继续向下查找；
            - 若元素是 list，也不会下钻该元素（同样视为叶子）。
        - 对其他类型（str/int/None 等）直接忽略。

    Args:
        数据 (Any): 任意嵌套数据结构，常见为 dict / list。

    Returns:
        List[list]:
            - 返回收集到的所有 list（保持发现顺序）。
            - 若没有命中，返回空列表。

    Notes:
        - “不下钻列表”策略可以避免 list 内部包含 dict 时造成过度遍历，
          适合你描述的：第一层提到列表就停。
        - 若同一个 list 对象在结构中被多处引用，默认只收集一次（按对象 id 去重）。
    """
    结果: List[list] = []
    已收集列表ID: Set[int] = set()

    def 递归(节点: Any) -> None:
        try:
            if isinstance(节点, dict):
                for 值 in 节点.values():
                    if isinstance(值, list):
                        列表ID = id(值)
                        if 列表ID not in 已收集列表ID:
                            已收集列表ID.add(列表ID)
                            结果.append(值)
                        # 命中 list：不下钻
                        continue

                    # 只继续遍历 dict / list（但 list 的下钻受规则控制）
                    if isinstance(值, (dict, list)):
                        递归(值)

            elif isinstance(节点, list):
                # list 作为容器：允许扫它的元素，但遇到元素是 list 时仍不下钻
                for 元素 in 节点:
                    if isinstance(元素, dict):
                        递归(元素)
                    elif isinstance(元素, list):
                        # 元素本身是 list：按规则不下钻
                        continue
                    else:
                        continue
            else:
                return
        except Exception:
            # 底层工具函数：异常吞掉，保持稳定
            return

    递归(数据)
    return 结果
