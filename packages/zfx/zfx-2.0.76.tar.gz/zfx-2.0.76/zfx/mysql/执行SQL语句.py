def 执行SQL语句(连接对象, 游标对象, sql语句, 参数=None):
    """
    执行给定的 SQL 语句，并返回结果或错误信息。

    参数：
        - 连接对象：已经建立的数据库连接对象。
        - 游标对象：通过连接对象获取的游标对象，用于执行查询或更新。
        - sql语句：要执行的 SQL 查询或更新语句。
        - 参数：可选，SQL 语句中占位符的值（如果有）。默认为 None。

    返回值：
        - 如果是查询语句（SELECT），返回查询结果。
        - 如果是更新、插入或删除等操作，返回操作是否成功的状态。
        - 如果发生异常，返回错误信息。

    使用示例：
        连接对象, 游标对象 = zfx_mysql.连接数据库("127.0.0.1", "root", "password", "test_db")

        # 执行查询
        结果 = zfx_mysql.执行SQL语句(连接对象, 游标对象, "SELECT * FROM `users` WHERE `age` > %s", (18,))
        print(结果)

        # 执行更新
        状态 = zfx_mysql.执行SQL语句(连接对象, 游标对象, "UPDATE `users` SET `age` = %s WHERE `id` = %s", (30, 1))
        print(状态)

    """
    try:
        # 如果参数存在，执行带参数的 SQL 语句
        if 参数:
            游标对象.execute(sql语句, 参数)
        else:
            # 执行不带参数的 SQL 语句
            游标对象.execute(sql语句)

        # 如果是查询操作（SELECT），返回查询结果
        if sql语句.strip().upper().startswith("SELECT"):
            结果 = 游标对象.fetchall()
            return 结果

        # 对于其他 SQL 操作（如 UPDATE, INSERT, DELETE），提交事务并返回成功标志
        else:
            连接对象.commit()  # 提交更改
            return "操作成功"

    except Exception as e:
        # 出现错误时，返回错误信息
        连接对象.rollback()  # 回滚事务
        return f"错误: {e}"