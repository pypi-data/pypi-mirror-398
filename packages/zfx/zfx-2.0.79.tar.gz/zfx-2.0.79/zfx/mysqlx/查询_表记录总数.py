from __future__ import annotations

import re
from typing import Optional


def 查询_表记录总数(
    连接对象,
    表名: str,
) -> Optional[int]:
    """查询指定 MySQL 表中的记录总数。

    功能说明:
        - 返回指定表的记录数量；
        - 若表不存在、查询失败或发生异常，返回 None；
        - 游标在函数内部创建并自动释放；
        - 不打印、不抛异常，适合作为底层工具函数。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。

    Returns:
        int | None:
            - 成功：返回记录总数。
            - 失败：返回 None。
    """
    try:
        # 表名安全校验，防止 SQL 注入
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return None

        with 连接对象.cursor() as 游标:
            游标.execute(f"SELECT COUNT(*) FROM `{表名}`")
            结果 = 游标.fetchone()

            if not 结果:
                return None

            return int(结果[0])

    except Exception:
        return None
