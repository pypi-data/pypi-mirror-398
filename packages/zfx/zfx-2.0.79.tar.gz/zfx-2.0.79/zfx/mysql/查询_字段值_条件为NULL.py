def 查询_字段值_条件为NULL(连接对象, 游标对象, 表名: str, 目标字段: str, 条件字段: str):
    """
    根据“某字段为 NULL”查找记录，并把目标字段的值全部取出来。
    无论查询是否成功，函数都会返回列表。如果发生任何异常，返回空列表。

    Args:
        连接对象: 已连接好的 MySQL 连接。
        游标对象: 用于执行 SQL 的游标。
        表名 (str): 要查询的表名。
        目标字段 (str): 要取出的字段名。
        条件字段 (str): 用来判断是否为 NULL 的字段名。

    Returns:
        list[str]: 字符串列表；若出错或无记录，返回空列表。
    """
    try:
        sql = f"SELECT `{目标字段}` FROM `{表名}` WHERE `{条件字段}` IS NULL;"
        游标对象.execute(sql)
        行列表 = 游标对象.fetchall()
        return [
            行[0] if isinstance(行, tuple) else list(行.values())[0]
            for 行 in 行列表
        ]
    except Exception:
        return []
