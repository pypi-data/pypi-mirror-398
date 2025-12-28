from __future__ import annotations

import re
from typing import Any, List


def 查询_字段全部值(
    连接对象,
    表名: str,
    字段名: str,
) -> List[Any]:
    """查询指定 MySQL 表中某个字段的全部值。

    功能说明:
        - 执行 SELECT 字段 FROM 表 的查询；
        - 返回该字段的所有值组成的列表；
        - 若表名/字段名非法、查询失败或发生异常，返回空列表；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。
        字段名 (str): 要提取的字段名（仅允许字母、数字、下划线）。

    Returns:
        list:
            - 成功：返回字段值列表，例如 ["a", "b", "c"]。
            - 失败或无数据：返回空列表。
    """
    try:
        # 表名 / 字段名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return []
        if not re.fullmatch(r"[A-Za-z0-9_]+", 字段名):
            return []

        sql = f"SELECT `{字段名}` FROM `{表名}`"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)
            结果 = 游标.fetchall() or []

        # fetchall 返回 [(value,), ...]
        return [行[0] for 行 in 结果]

    except Exception:
        return []