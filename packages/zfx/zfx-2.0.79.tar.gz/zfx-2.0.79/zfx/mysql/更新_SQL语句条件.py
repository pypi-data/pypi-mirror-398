def 更新_SQL语句条件(连接对象, 表名, 值字典, 条件):
    """
    根据给定的表名、值字典和条件更新数据库表中的数据。

    参数：
        - 连接对象：数据库连接对象。
        - 表名：要更新的表名。
        - 值字典：包含列名和对应更新值的字典，格式为 {'列名1': 值1, '列名2': 值2}。
        - 条件：用于指定更新条件的 SQL WHERE 字符串，例如 "id = 1"。

    条件格式示例：
        - 查询某个字段等于特定值：
            条件 = "id = 1"
        - 查询某个字段值在特定范围内：
            条件 = "age BETWEEN 20 AND 30"
        - 查询某个字段包含特定值（字符串匹配）：
            条件 = "name LIKE '%John%'"
        - 查询多个条件组合：
            条件 = "age > 30 AND city = 'Beijing'"
        - 查询某个字段值在一组值中：
            条件 = "id IN (1, 2, 3)"
        - 查询日期范围：
            条件 = "created_at >= '2023-01-01' AND created_at <= '2023-12-31'"

    返回值：
        - 更新成功返回 True，失败返回 False。

    使用示例（可以复制并直接修改）：
        更新结果 = zfx_mysql.更新_SQL语句条件(连接对象, "users", {"name": "John Doe", "email": "john@example.com"}, "id = 1")

        # 替换参数：
        # - 连接对象：已建立的数据库连接对象
        # - 表名：要更新的表名称，如 "users" 或 "orders"
        # - 值字典：包含要更新的列和值的字典，如 {"name": "John Doe", "email": "john@example.com"}
        # - 条件：更新的条件字符串，如 "id = 1"

        # 使用返回结果：
        # if 更新结果:
        #     print("更新成功")
        # else:
        #     print("更新失败")
    """
    游标对象 = None
    try:
        # 构造 SQL 的 SET 部分，将字典中的键值对转换成列和值的占位符
        set_clause = ', '.join([f"{key} = %s" for key in 值字典.keys()])

        # 构造完整的 SQL 语句，使用占位符 %s 避免 SQL 注入
        sql = f"UPDATE {表名} SET {set_clause} WHERE {条件};"

        # 获取游标对象，用于执行 SQL 语句
        游标对象 = 连接对象.cursor()

        # 执行 SQL 语句，值通过参数化方式传递，自动转义
        游标对象.execute(sql, tuple(值字典.values()))

        # 提交事务，确保更改生效
        连接对象.commit()

        return True
    except Exception as e:
        return False
    finally:
        # 如果游标对象存在，关闭游标，释放资源
        if 游标对象:
            游标对象.close()

