from __future__ import annotations

import re


def 删除记录(
    连接对象,
    表名: str,
    条件: str,
) -> bool:
    """从指定表中删除符合条件的记录。

    功能说明:
        - 使用 DELETE FROM ... WHERE ... 删除记录；
        - 条件为原生 SQL WHERE 子句（不包含 WHERE 关键字）；
        - 至少删除一条记录才返回 True；
        - 未命中任何记录或发生异常返回 False；
        - 游标在函数内部创建并自动释放。

    ⚠ 风险提示:
        - 若 条件 为 "1=1"，将删除整张表的数据；
        - 请确保 条件 来自可信代码。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要操作的表名（仅允许字母、数字、下划线）。
        条件 (str): 原生 SQL WHERE 条件字符串，例如：
            - "id = 5"
            - "price < 10 AND region = 'US'"
            - "updated_at < '2025-01-01'"

    Returns:
        bool:
            - True  : 至少删除了一条记录。
            - False : 未删除任何记录、参数非法或发生异常。
    """
    try:
        # 基本校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return False
        if not isinstance(条件, str) or not 条件.strip():
            return False

        sql = f"DELETE FROM `{表名}` WHERE {条件}"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)
            影响行数 = 游标.rowcount

        连接对象.commit()
        return 影响行数 > 0

    except Exception:
        try:
            连接对象.rollback()
        except Exception:
            pass
        return False
