from __future__ import annotations

import re
from typing import Any, Optional, Tuple


def 查询_最后一条记录(
    连接对象,
    表名: str,
) -> Optional[Tuple[Any, ...]]:
    """查询指定 MySQL 表中按 id 倒序的最后一条记录。

    功能说明:
        - 按 id 字段倒序排序，取第一条记录；
        - 适用于表中存在自增主键 id 的常见结构；
        - 若表为空、表名非法或查询失败，返回 None；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。

    Returns:
        tuple | None:
            - 成功：返回最后一条记录（tuple）。
            - 失败或无数据：返回 None。

    Notes:
        - 本函数假设表中存在名为 `id` 的可排序字段；
        - 若表无 id 字段或需要按其他字段排序，
          请使用更通用的排序查询函数（例如按时间字段）。
    """
    try:
        # 表名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return None

        sql = f"SELECT * FROM `{表名}` ORDER BY `id` DESC LIMIT 1"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)
            return 游标.fetchone()

    except Exception:
        return None
