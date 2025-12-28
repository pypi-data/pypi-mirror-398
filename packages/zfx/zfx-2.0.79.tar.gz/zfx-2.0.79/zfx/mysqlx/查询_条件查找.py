from __future__ import annotations

import re
from typing import Any, List, Tuple


def 查询_条件查找(
    连接对象,
    表名: str,
    条件: str,
) -> List[Tuple[Any, ...]]:
    """根据给定条件查询指定 MySQL 表的记录。

    功能说明:
        - 使用原生 SQL 条件字符串进行查询；
        - 条件语法需完全符合 MySQL WHERE 子句规则；
        - 查询成功返回记录列表；
        - 查询失败、条件非法或发生异常时返回空列表；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。
        条件 (str): WHERE 子句中的条件字符串（不包含 WHERE 关键字）。

    Returns:
        list[tuple]:
            - 成功：返回满足条件的记录列表。
            - 失败或无数据：返回空列表。

    Notes:
        - 本函数不会对条件字符串做任何转义或安全处理；
        - 仅建议在“条件字符串来自可信代码”的场景中使用；
        - 若条件来源于用户输入，请使用参数化查询的安全版本。
    """
    try:
        # 表名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return []

        # 条件最基本校验（避免空 WHERE）
        if not isinstance(条件, str) or not 条件.strip():
            return []

        sql = f"SELECT * FROM `{表名}` WHERE {条件}"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)
            return 游标.fetchall() or []

    except Exception:
        return []
