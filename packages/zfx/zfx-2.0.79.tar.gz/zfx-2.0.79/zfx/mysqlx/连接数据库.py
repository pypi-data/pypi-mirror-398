from __future__ import annotations
from typing import Optional
import pymysql
from pymysql.connections import Connection


def 连接数据库(
    主机: str,
    用户名: str,
    密码: str,
    数据库名: str,
    字符集: str = "utf8mb4",
    端口: int = 3306,
    *,
    自动提交: bool = True,
    连接超时秒: int = 10,
    读超时秒: int = 30,
    写超时秒: int = 30,
) -> Optional[Connection]:
    """创建 MySQL 连接并返回连接对象（PyMySQL），老版本mysql库计划2026年正式淘汰删除。

    功能说明:
        - 建立与 MySQL 数据库的连接；
        - 成功返回连接对象，失败返回 None；
        - 只暴露“连接对象”，游标由后续操作函数内部管理；
        - 异常安全：不抛异常、不打印错误。

    Args:
        主机 (str): 数据库主机名或 IP 地址。
        用户名 (str): 数据库用户名。
        密码 (str): 数据库密码。
        数据库名 (str): 数据库名称。
        字符集 (str): 使用的字符集，默认 utf8mb4。
        端口 (int): MySQL 端口号，默认 3306。
        自动提交 (bool): 是否启用 autocommit，默认 True。
        连接超时秒 (int): 连接超时秒数，默认 10。
        读超时秒 (int): 读取超时秒数，默认 30。
        写超时秒 (int): 写入超时秒数，默认 30。

    Returns:
        Connection | None:
            - 成功：返回 MySQL 连接对象。
            - 失败：返回 None。

    Notes:
        - 本函数只负责“创建连接”，不负责任何 SQL 执行。
        - 使用完成后，请在业务层主动关闭连接：
            连接对象.close()
        - 推荐所有 SQL 操作通过 zfx.mysql 的执行函数完成，
          不在业务层直接操作 cursor。
    """
    try:
        连接对象 = pymysql.connect(
            host=主机,
            user=用户名,
            password=密码,
            database=数据库名,
            port=端口,
            charset=字符集,
            autocommit=自动提交,
            connect_timeout=连接超时秒,
            read_timeout=读超时秒,
            write_timeout=写超时秒,
        )
        return 连接对象
    except Exception:
        return None