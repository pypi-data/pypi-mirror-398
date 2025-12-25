from typing import Any, List


def 取包含文本的成员(
    数据: List[Any],
    文本: str,
    模式: str = "成员",
) -> List[Any]:
    """
    从列表（支持嵌套）中取出包含指定文本内容的成员。

    功能说明：
        - 支持两种模式：
            1) 模式="成员"：
               递归遍历所有层级，仅对字符串进行匹配，返回命中的字符串成员列表。
            2) 模式="第一层"：
               仅遍历第一层；把每个第一层成员视为一个整体：
               - 若该成员是字符串：直接做包含匹配；
               - 若该成员是列表：递归检查其内部任意字符串是否包含文本；
               命中则返回该第一层成员（可能是字符串或子列表）。

        - 不修改原数据；
        - 不抛异常、不打印日志。

    Args:
        数据 (list): 可能包含嵌套列表的列表结构。
        文本 (str): 需要匹配的文本内容。
        模式 (str): "成员" 或 "第一层"。

    Returns:
        list[Any]:
            - 模式="成员"：返回 list[str]（命中的字符串）
            - 模式="第一层"：返回 list[Any]（命中的第一层成员）
            - 参数非法或无匹配：返回空列表 []
    """
    try:
        if not isinstance(数据, list):
            return []

        if not isinstance(文本, str) or 文本 == "":
            return []

        if 模式 not in ("成员", "第一层"):
            return []

        def _列表内是否包含文本(当前列表: List[Any]) -> bool:
            """递归检查列表内部任意字符串是否包含文本。"""
            for 项 in 当前列表:
                if isinstance(项, str):
                    if 文本 in 项:
                        return True
                elif isinstance(项, list):
                    if _列表内是否包含文本(项):
                        return True
            return False

        结果: List[Any] = []

        if 模式 == "成员":
            def _递归收集字符串(当前列表: List[Any]) -> None:
                for 项 in 当前列表:
                    if isinstance(项, str):
                        if 文本 in 项:
                            结果.append(项)
                    elif isinstance(项, list):
                        _递归收集字符串(项)

            _递归收集字符串(数据)
            return 结果

        # 模式 == "第一层"
        for 第一层项 in 数据:
            if isinstance(第一层项, str):
                if 文本 in 第一层项:
                    结果.append(第一层项)
            elif isinstance(第一层项, list):
                if _列表内是否包含文本(第一层项):
                    结果.append(第一层项)

        return 结果
    except Exception:
        return []