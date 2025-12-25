def 查询_最后一条记录(连接对象, 表名):
    """
    查询指定表的最后一条记录。

    参数：
        - 连接对象：与数据库的连接对象。
        - 表名：要查询最后一条记录的表名。

    返回值：
        - 最后一条记录：表中的最后一条记录，如果查询失败则返回 None。

    使用示例（可以复制并直接修改）：
        最后一条记录 = zfx_mysql.查询_最后一条记录(连接对象, "users")

        # 替换参数：
        # - 连接对象：已建立的数据库连接对象
        # - 表名：要查询最后一条记录的表名称，如 "users" 或 "orders"

        # 使用查询返回的最后一条记录：
        # if 最后一条记录 is not None:
        #     print("最后一条记录:", 最后一条记录)
        # else:
        #     print("查询失败")
    """
    游标对象 = None
    try:
        游标对象 = 连接对象.cursor()
        游标对象.execute(f"SELECT * FROM {表名} ORDER BY id DESC LIMIT 1")
        最后一条记录 = 游标对象.fetchone()
        return 最后一条记录
    except Exception:
        return None
    finally:
        if 游标对象:
            游标对象.close()