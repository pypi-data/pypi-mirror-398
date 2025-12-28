from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple


def 执行SQL_查询(
    连接对象,
    SQL: str,
    参数: Optional[Sequence[Any]] = None,
) -> List[Tuple[Any, ...]]:
    """执行 SELECT 查询并返回结果列表。

    功能说明:
        - 用于执行 SELECT 类查询；
        - 返回 fetchall() 的结果（list[tuple]）；
        - 任何异常返回空列表；
        - 不打印、不抛异常。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        SQL (str): 要执行的 SQL 语句（建议为 SELECT）。
        参数 (Sequence[Any] | None): 参数化占位符对应的值。

    Returns:
        list[tuple]:
            - 成功：查询结果列表。
            - 失败：空列表。
    """
    try:
        if not isinstance(SQL, str) or not SQL.strip():
            return []

        with 连接对象.cursor() as 游标:
            if 参数 is not None:
                游标.execute(SQL, tuple(参数))
            else:
                游标.execute(SQL)
            return 游标.fetchall() or []

    except Exception:
        return []