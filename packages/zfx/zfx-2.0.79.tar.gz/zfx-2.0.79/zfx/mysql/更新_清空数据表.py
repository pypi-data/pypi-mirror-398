def 更新_清空数据表(连接对象, 表名):
    """
    清空整个表的所有数据。

    参数：
        - 连接对象: 数据库连接对象。
        - 表名: 需要清空数据的表的名称。

    返回值：
        - 清空成功返回 True，失败返回 False。

    使用示例（可以复制并直接修改）：
        更新结果 = zfx_mysql.更新_清空数据表(连接对象, "users")

        # 替换参数：
        # - 连接对象：已建立的数据库连接对象
        # - 表名：要清空数据的表名称，如 "users" 或 "orders"

        # 使用返回结果：
        # if 更新结果:
        #     print("表数据已成功清空")
        # else:
        #     print("清空表数据失败")
    """
    游标 = None
    try:
        # 构造 TRUNCATE TABLE 语句以清空表的数据
        sql = f"TRUNCATE TABLE {表名};"

        # 获取游标对象，用于执行 SQL 语句
        游标 = 连接对象.cursor()
        # 执行 SQL 语句
        游标.execute(sql)
        # 提交事务，确保更改生效
        连接对象.commit()
        return True
    except Exception as e:
        return False
    finally:
        # 如果游标对象存在，关闭游标，释放资源
        if 游标:
            游标.close()