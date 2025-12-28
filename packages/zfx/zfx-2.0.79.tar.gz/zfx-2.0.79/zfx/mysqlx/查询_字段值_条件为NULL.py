from __future__ import annotations

import re
from typing import Any, List


def 查询_字段值_条件为NULL(
    连接对象,
    表名: str,
    目标字段: str,
    条件字段: str,
) -> List[Any]:
    """查询指定表中“条件字段为 NULL”的记录，并返回目标字段的值列表。

    功能说明:
        - 执行形如：
              SELECT 目标字段 FROM 表名 WHERE 条件字段 IS NULL
        - 返回目标字段的所有值；
        - 若无记录、表/字段非法或发生异常，返回空列表；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。
        目标字段 (str): 要提取值的字段名（仅允许字母、数字、下划线）。
        条件字段 (str): 用于判断是否为 NULL 的字段名（仅允许字母、数字、下划线）。

    Returns:
        list:
            - 成功：返回目标字段值列表。
            - 失败或无数据：返回空列表。
    """
    try:
        # 表名 / 字段名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return []
        if not re.fullmatch(r"[A-Za-z0-9_]+", 目标字段):
            return []
        if not re.fullmatch(r"[A-Za-z0-9_]+", 条件字段):
            return []

        sql = (
            f"SELECT `{目标字段}` "
            f"FROM `{表名}` "
            f"WHERE `{条件字段}` IS NULL"
        )

        with 连接对象.cursor() as 游标:
            游标.execute(sql)
            结果 = 游标.fetchall() or []

        # fetchall 统一视为 [(value,), ...]
        return [行[0] for 行 in 结果]

    except Exception:
        return []