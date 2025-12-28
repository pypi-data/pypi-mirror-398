from __future__ import annotations

import re
from typing import Any, Optional, Tuple


def 查询_第一条记录(
    连接对象,
    表名: str,
) -> Optional[Tuple[Any, ...]]:
    """查询指定 MySQL 表中的第一条记录。

    功能说明:
        - 从指定表中取出第一条记录（无排序条件）；
        - 若表为空、查询失败或发生异常，返回 None；
        - 游标在函数内部创建并自动释放；
        - 不打印、不抛异常，适合作为底层工具函数。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。

    Returns:
        tuple | None:
            - 成功：返回第一条记录（tuple）。
            - 失败或无数据：返回 None。
    """
    try:
        # 表名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return None

        with 连接对象.cursor() as 游标:
            游标.execute(f"SELECT * FROM `{表名}` LIMIT 1")
            return 游标.fetchone()

    except Exception:
        return None