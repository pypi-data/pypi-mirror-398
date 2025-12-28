import mysql.connector


def 连接数据库(主机, 用户名, 密码, 数据库名, 字符集='utf8mb4'):
    """
    功能：
        建立与 MySQL 数据库的连接，并返回中文对象（连接对象与游标对象）。
        本函数基于官方驱动 mysql-connector-python 编写。
        适用于 MySQL 5.7 及以下版本。
        ⚠ 注意：不支持 MySQL 8.x 的 caching_sha2_password 认证方式。

    参数：
        - 主机 (str)：数据库主机名或 IP 地址。
        - 用户名 (str)：数据库用户名。
        - 密码 (str)：数据库密码。
        - 数据库名 (str)：要连接的数据库名称。
        - 字符集 (str)：使用的字符集编码，默认 "utf8mb4"，兼容 "utf8"。

    返回值：
        - 成功时返回 (连接对象, 游标对象)。
        - 失败时返回 (None, None)

    使用示例：
        结果 = 连接数据库("127.0.0.1", "root", "123456", "test_db")
        if 结果:
            连接对象, 游标对象 = 结果
            游标对象.execute("SELECT NOW() AS 当前时间;")
            print(游标对象.fetchone())
        else:
            print("数据库连接失败。")

    内部说明：
        1) 使用 mysql-connector-python 官方驱动；
           安装命令一：pip install mysql-connector-python
           安装命令二：pip install mysql-connector
        2) 默认使用 utf8mb4 字符集，支持中英文混合。
        3) 本函数**不支持 MySQL 8.x 的 caching_sha2_password 认证方式**。
           若目标数据库为 MySQL 8.x，请将用户认证插件改为 mysql_native_password：
               ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '密码';
               FLUSH PRIVILEGES;
        4) 出现异常时会打印错误信息，并返回 None。
    """
    try:
        连接对象 = mysql.connector.connect(
            host=主机,
            user=用户名,
            password=密码,
            database=数据库名,
            charset=字符集
        )

        游标对象 = 连接对象.cursor()
        return 连接对象, 游标对象

    except Exception as e:
        print(f"数据库连接失败：{e}")
        return None, None
