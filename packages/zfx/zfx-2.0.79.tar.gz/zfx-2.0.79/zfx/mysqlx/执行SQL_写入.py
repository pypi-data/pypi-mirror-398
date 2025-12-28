from __future__ import annotations

from typing import Any, Optional, Sequence


def 执行SQL_写入(
    连接对象,
    SQL: str,
    参数: Optional[Sequence[Any]] = None,
    *,
    失败回滚: bool = True,
) -> bool:
    """执行写入类 SQL（UPDATE/INSERT/DELETE/TRUNCATE 等）。

    功能说明:
        - 执行写入类 SQL；
        - 成功 commit 并返回 True；
        - 失败可选 rollback 并返回 False；
        - 不打印、不抛异常。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        SQL (str): 写入类 SQL 语句。
        参数 (Sequence[Any] | None): 参数化占位符对应的值。
        失败回滚 (bool): 失败时是否 rollback。

    Returns:
        bool:
            - True  : 执行成功并已提交。
            - False : 执行失败（可已回滚）。
    """
    try:
        if not isinstance(SQL, str) or not SQL.strip():
            return False

        with 连接对象.cursor() as 游标:
            if 参数 is not None:
                游标.execute(SQL, tuple(参数))
            else:
                游标.execute(SQL)

        连接对象.commit()
        return True

    except Exception:
        if 失败回滚:
            try:
                连接对象.rollback()
            except Exception:
                pass
        return False
