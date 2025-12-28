def 数据库连接_是否活跃(连接对象) -> bool:
    """
    功能：
        检查指定的 MySQL 数据库连接是否仍处于活跃状态（未断开、未超时、未被服务器关闭）。
        本函数基于 mysql-connector-python 驱动的内置机制实现，适用于 MySQL 5.7 与 8.x 系列。

    参数：
        连接对象 (mysql.connector.connection.MySQLConnection):
            由 mysql.connector.connect() 创建的数据库连接对象。
            若传入的对象为 None，将直接返回 False。

    返回：
        bool:
            - True：连接有效，可正常执行 SQL。
            - False：连接无效（可能已断开、超时、或因网络问题失效）。

    使用示例：
        连接对象, 游标对象 = 连接数据库("127.0.0.1", "root", "123456", "test_db")
        if not 数据库连接_是否活跃(连接对象):
            连接对象, 游标对象 = 连接数据库("127.0.0.1", "root", "123456", "test_db")
        游标对象.execute("SELECT NOW();")
        print(游标对象.fetchone())

    内部说明：
        1. 函数主要利用 mysql.connector 提供的两个核心机制：
           - is_connected()：检测连接对象当前是否仍标记为“连接中”。
           - ping()：向数据库发送轻量级心跳包，用于验证连接是否真的可用。

        2. ping(reconnect=False, attempts=1, delay=0)
           - reconnect=False 表示不自动重连，只检测状态；
           - attempts=1, delay=0 代表只尝试一次，不等待；
           - 调用 ping() 会触发一次真实的服务器交互。
             若成功，则说明连接可用；
             若失败，将抛出异常（被本函数捕获并返回 False）。

        3. 关于 MySQL 超时机制：
           - MySQL 服务器默认 wait_timeout = 28800 秒（8 小时）。
           - 每当客户端执行任何操作（包括 ping），计时会被重置。
           - 因此，定期调用本函数相当于“续命”操作，可防止长连接超时断开。

        4. 建议调用频率：
           - 对于持续运行的服务（如采集程序、调度器等），
             建议每隔 5~30 分钟调用一次本函数，保持连接活跃。

        5. 安全性：
           - 函数内部包含完整异常捕获，不会抛出未处理错误。
           - 若出现任何异常（如网络断线、MySQL 重启、认证失效），将返回 False。

    实现逻辑：
        1) 若连接对象为 None，则立即返回 False；
        2) 调用 is_connected() 检查标志；
        3) 若标志为真，则执行 ping()；
        4) 若 ping() 正常完成，则返回 True；
        5) 任意异常均视为连接失效，返回 False。
    """
    try:
        if 连接对象 is None:
            return False

        if 连接对象.is_connected():
            # 发送轻量心跳包，验证连接可用性
            连接对象.ping(reconnect=False, attempts=1, delay=0)
            return True
        else:
            return False

    except Exception:
        return False
