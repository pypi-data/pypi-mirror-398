def 查询_字段全部值(连接对象, 游标对象, 表名: str, 字段名: str):
    """
    查询指定表中某字段的全部值，并以列表形式返回。

    功能说明：
        执行 SQL 查询，例如：
            SELECT `字段名` FROM `表名`;
        fetchall() 返回元组列表（如: ('abc',), ('def',)），
        因此使用行[0] 获取字段值。
        若查询失败（例如字段不存在、表不存在、数据库异常等），
        则返回空列表以避免程序中断。

    Args:
        连接对象: MySQL 的连接对象。
        游标对象: MySQL 的游标对象。
        表名 (str): 要查询的表名。
        字段名 (str): 要提取的字段名。

    Returns:
        list: 字段值列表；在异常情况下返回空列表。
    """
    try:
        sql = f"SELECT `{字段名}` FROM `{表名}`;"
        游标对象.execute(sql)
        结果 = 游标对象.fetchall()
        return [行[0] for 行 in 结果]
    except Exception:
        return []
