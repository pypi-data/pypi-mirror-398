def 删除记录(连接对象, 游标对象, 表名: str, 条件: str) -> bool:
    """
    从指定表中删除符合条件的记录，支持原生 MySQL 条件格式。

    Args:
        连接对象: 已建立的数据库连接对象。
        游标对象: 数据库游标对象，用于执行 SQL 语句。
        表名 (str): 要操作的表名，例如 "games"。
        条件 (str): 删除条件（原生 MySQL 语法），例如：
            - "id = 5"                                → 删除 id 为 5 的记录
            - "product_url = 'https://example.com'"   → 删除指定产品链接
            - "region = 'US' AND price < 10"          → 删除符合多个条件的记录
            - "title LIKE '%Mario%'"                  → 删除标题中包含 “Mario” 的记录
            - "updated_at < '2025-01-01'"             → 删除更新时间早于 2025-01-01 的记录
            - "1=1"                                   → 删除整张表（危险操作，慎用！）

    Returns:
        bool: 删除结果。
            - True：删除成功（至少删除一条记录）。
            - False：删除失败或发生异常。

    Example:
        删除记录(连接对象, 游标对象, "games", "product_url = 'https://example.com'")
    """
    try:
        sql语句 = f"DELETE FROM {表名} WHERE {条件}"
        游标对象.execute(sql语句)
        连接对象.commit()
        return 游标对象.rowcount > 0
    except Exception:
        连接对象.rollback()
        return False