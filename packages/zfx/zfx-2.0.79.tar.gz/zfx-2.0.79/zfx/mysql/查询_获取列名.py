def 查询_获取列名(连接对象, 表名):
    """
    获取指定表的所有列名(简单的说就是看有些什么字段)。

    参数：
        - 连接对象：与数据库的连接对象。
        - 表名：要获取列名的表名。

    返回值：
        - 列名列表：包含所有列名的列表，如果查询失败则返回 None。

    使用示例（可以复制并直接修改）：
        列名列表 = zfx_mysql.查询_获取列名(连接对象, "users")

        # 替换参数：
        # - 连接对象：已建立的数据库连接对象
        # - 表名：要获取列名的表名称，如 "users" 或 "orders"

        # 使用返回的列名列表：
        # if 列名列表 is not None:
        #     print("表的列名:", 列名列表)
        # else:
        #     print("查询失败")
    """
    游标对象 = None
    try:
        游标对象 = 连接对象.cursor()
        游标对象.execute(f"DESCRIBE {表名}")
        列名列表 = [row[0] for row in 游标对象.fetchall()]
        return 列名列表
    except Exception:
        return None
    finally:
        if 游标对象:
            游标对象.close()