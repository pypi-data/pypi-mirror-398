def 查询_表结构(连接对象, 游标对象, 表名: str):
    """
    查询指定数据表的结构信息，并以列表形式返回。

    功能说明：
        执行 DESCRIBE 语句，例如：
            DESCRIBE `表名`;
        返回字段名称、类型、是否允许 NULL、键类型、默认值等信息。
        若查询失败（例如表不存在或数据库异常），
        则返回空列表以避免程序中断。

    Args:
        连接对象: MySQL 的连接对象。
        游标对象: MySQL 的游标对象。
        表名 (str): 需要查询的表名。

    Returns:
        list: 包含字段结构信息的列表，每项为一个字典。
              例如：
              [
                  {
                      "Field": "id",
                      "Type": "int(11)",
                      "Null": "NO",
                      "Key": "PRI",
                      "Default": None,
                      "Extra": "auto_increment"
                  },
                  ...
              ]
              异常情况下返回空列表。
    """
    try:
        sql = f"DESCRIBE `{表名}`;"
        游标对象.execute(sql)
        结果 = 游标对象.fetchall()

        return [
            {
                "Field": 行[0],
                "Type": 行[1],
                "Null": 行[2],
                "Key": 行[3],
                "Default": 行[4],
                "Extra": 行[5],
            }
            for 行 in 结果
        ]
    except Exception:
        return []