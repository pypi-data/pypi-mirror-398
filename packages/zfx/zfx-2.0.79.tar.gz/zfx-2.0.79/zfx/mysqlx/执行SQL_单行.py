from __future__ import annotations

from typing import Any, Optional, Sequence, Tuple


def 执行SQL_单行(
    连接对象,
    SQL: str,
    参数: Optional[Sequence[Any]] = None,
) -> Optional[Tuple[Any, ...]]:
    """执行 SELECT 查询并返回单行结果。

    功能说明:
        - 用于执行预期只取一行的 SELECT（通常配合 LIMIT 1）；
        - 成功返回 tuple，未命中返回 None；
        - 异常返回 None。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        SQL (str): 要执行的 SQL 语句（建议为 SELECT ... LIMIT 1）。
        参数 (Sequence[Any] | None): 参数化占位符对应的值。

    Returns:
        tuple | None:
            - 成功命中：返回一行 tuple。
            - 未命中/失败：返回 None。
    """
    try:
        if not isinstance(SQL, str) or not SQL.strip():
            return None

        with 连接对象.cursor() as 游标:
            if 参数 is not None:
                游标.execute(SQL, tuple(参数))
            else:
                游标.execute(SQL)
            return 游标.fetchone()

    except Exception:
        return None
