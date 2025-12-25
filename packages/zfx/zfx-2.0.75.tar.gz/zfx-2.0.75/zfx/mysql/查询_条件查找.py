def 查询_条件查找(连接对象, 表名, 条件):
    """
    根据条件查询指定表的记录。

    参数：
        - 连接对象：与数据库的连接对象。
        - 表名 (str)：要查询的表名。
        - 条件 (str)：用于查询记录的条件字符串（严格遵守 MySQL 原生格式条件）。

    条件格式示例：
        - 查询某个字段等于特定值：
            条件 = "age = 25"
        - 查询某个字段值在特定范围内：
            条件 = "age BETWEEN 20 AND 30"
        - 查询某个字段包含特定值（字符串匹配）：
            条件 = "name LIKE '%John%'"
        - 查询多个条件组合：
            条件 = "age > 30 AND city = 'Beijing'"
        - 查询某个字段值在一组值中：
            条件 = "id IN (1, 2, 3, 4)"
        - 查询日期范围：
            条件 = "date >= '2023-01-01' AND date <= '2023-12-31'"

    返回值：
        - 记录列表 (list)：满足条件的记录列表，如果查询失败则返回 None。

    使用示例（可以复制并直接修改）：
        记录列表 = zfx_mysql.查询_条件查找(连接对象, "users", "age > 30")

        # 替换参数：
        # - 连接对象：已建立的数据库连接对象
        # - 表名：要查询的表名称，如 "users" 或 "orders"
        # - 条件：用于查询的 SQL 条件字符串，如 "age > 30"

        # 使用查询返回的记录列表：
        # if 记录列表 is not None:
        #     for 记录 in 记录列表:
        #         print(记录)
        # else:
        #     print("查询失败")
    """
    游标对象 = None
    try:
        游标对象 = 连接对象.cursor()
        游标对象.execute(f"SELECT * FROM {表名} WHERE {条件}")
        记录列表 = 游标对象.fetchall()
        return 记录列表
    except Exception:
        return None
    finally:
        if 游标对象:
            游标对象.close()