from __future__ import annotations


def 数据库连接_是否活跃(连接对象) -> bool:
    """检查 PyMySQL 数据库连接是否仍处于活跃状态。

    功能说明:
        - 基于 PyMySQL 的 ping() 方法实现连接存活检测；
        - 不自动重连，仅检测当前连接是否可用；
        - 若连接对象为 None、已关闭或网络异常，返回 False；
        - 调用成功即视为连接活跃，并会刷新 MySQL 的 wait_timeout 计时。

    Args:
        连接对象:
            PyMySQL 创建的数据库连接对象。
            若为 None，直接返回 False。

    Returns:
        bool:
            - True  : 连接有效，可继续使用。
            - False : 连接无效、已断开或发生异常。

    Notes:
        - PyMySQL 中不存在 is_connected() 方法；
        - ping() 会向服务器发送轻量级心跳请求；
        - reconnect=False 表示不尝试自动重连，只做状态检测；
        - 建议在长时间运行的程序中定期调用本函数以保持连接活跃。
    """
    try:
        if not 连接对象:
            return False

        # PyMySQL：ping 成功即代表连接可用
        连接对象.ping(reconnect=False)
        return True

    except Exception:
        return False
