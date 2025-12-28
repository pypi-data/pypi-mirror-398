from __future__ import annotations

import re
from typing import Optional


def 查询_唯一值数量(
    连接对象,
    表名: str,
    字段名: str,
) -> Optional[int]:
    """查询指定 MySQL 表中某字段的唯一值数量。

    功能说明:
        - 执行 COUNT(DISTINCT 字段名) 统计唯一值数量；
        - 成功返回唯一值数量（可能为 0）；
        - 表名/字段名非法、查询失败或发生异常时返回 None；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。
        字段名 (str): 要统计唯一值数量的字段名（仅允许字母、数字、下划线）。

    Returns:
        int | None:
            - 成功：返回唯一值数量（>= 0）。
            - 失败：返回 None。
    """
    try:
        # 表名 / 字段名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return None
        if not re.fullmatch(r"[A-Za-z0-9_]+", 字段名):
            return None

        sql = f"SELECT COUNT(DISTINCT `{字段名}`) FROM `{表名}`"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)
            结果 = 游标.fetchone()

        if not 结果:
            return None

        return int(结果[0])

    except Exception:
        return None
