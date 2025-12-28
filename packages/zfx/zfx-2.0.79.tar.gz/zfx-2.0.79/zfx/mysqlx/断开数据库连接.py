from __future__ import annotations


def 断开数据库连接(连接对象) -> bool:
    """断开 MySQL 数据库连接。

    功能说明:
        - 安全关闭数据库连接对象；
        - 若连接对象为 None 或已关闭，视为成功；
        - 不处理游标（游标由各函数内部自行管理）；
        - 不抛异常、不打印错误。

    Args:
        连接对象: MySQL 数据库连接对象。

    Returns:
        bool:
            - True  : 连接已成功关闭或无需关闭。
            - False : 关闭过程中发生异常。
    """
    try:
        if 连接对象:
            连接对象.close()
        return True
    except Exception:
        return False
