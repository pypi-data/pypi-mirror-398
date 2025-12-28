from __future__ import annotations

from typing import List


def 查询_取所有表名(
    连接对象,
) -> List[str]:
    """查询并返回当前数据库中的所有表名。

    功能说明:
        - 执行 SHOW TABLES 查询当前数据库中的所有表；
        - 成功返回表名字符串列表；
        - 查询失败或发生异常时返回空列表；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。

    Returns:
        list[str]:
            - 成功：返回表名列表，例如 ["users", "orders"]。
            - 失败或无表：返回空列表。
    """
    try:
        with 连接对象.cursor() as 游标:
            游标.execute("SHOW TABLES")
            结果 = 游标.fetchall() or []

        # SHOW TABLES 返回 [(table_name,), ...]
        return [行[0] for 行 in 结果]

    except Exception:
        return []
