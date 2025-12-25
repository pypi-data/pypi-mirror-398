def 更新_指定字段空值填充(连接对象, 表名, 字段名, 填充数据):
    """
    填充某个字段的空值（NULL 或空字符串）。

    参数：
        - 连接对象: 数据库连接对象。
        - 表名: 需要更新的表的名称。
        - 字段名: 需要填充空值的字段名称。
        - 填充数据: 用于填充的值，可以是字符串或数值。

    返回值：
        - 更新成功返回 True，失败返回 False。

    使用示例（可以复制并直接修改）：
        更新结果 = zfx_mysql.更新_指定字段空值填充(连接对象, "users", "email", "default@example.com")

        # 替换参数：
        # - 连接对象：已建立的数据库连接对象
        # - 表名：要更新的表名称，如 "users" 或 "orders"
        # - 字段名：需要填充空值的字段名称，如 "email" 或 "phone"
        # - 填充数据：要用于填充的值，如 "default@example.com" 或 0

        # 使用返回结果：
        # if 更新结果:
        #     print(f"{字段名} 字段的空值已成功填充为 {填充数据}")
        # else:
        #     print("填充空值失败")
    """
    游标 = None
    try:
        # 构造完整的更新 SQL 语句，将字段的空值替换为填充值
        sql = f"UPDATE {表名} SET {字段名} = '{填充数据}' WHERE {字段名} IS NULL OR {字段名} = '';"

        # 获取游标对象，用于执行 SQL 语句
        游标 = 连接对象.cursor()
        # 执行 SQL 语句
        游标.execute(sql)
        # 提交事务，确保更改生效
        连接对象.commit()
        return True
    except Exception:
        return False
    finally:
        # 如果游标对象存在，关闭游标，释放资源
        if 游标:
            游标.close()