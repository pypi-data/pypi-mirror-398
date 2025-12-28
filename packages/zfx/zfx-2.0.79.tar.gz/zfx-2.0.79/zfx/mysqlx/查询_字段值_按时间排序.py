from __future__ import annotations

import re
from typing import Any, List, Optional


def 查询_字段值_按时间排序(
    连接对象,
    表名: str,
    目标字段: str,
    时间字段: str,
    *,
    限制条数: Optional[int] = None,
    是否最新优先: bool = True,
) -> List[Any]:
    """按时间字段排序，批量取出目标字段的值列表。

    功能说明:
        - 按指定时间字段排序，从表中批量取出目标字段的值；
        - 是否最新优先=True  → ORDER BY 时间字段 DESC（最新在前）
          是否最新优先=False → ORDER BY 时间字段 ASC（最旧在前）
        - 限制条数为 None 时不加 LIMIT，返回全部；
        - 默认过滤时间字段为 NULL 的记录（WHERE 时间字段 IS NOT NULL）；
        - 异常安全：任何异常返回空列表，不打印、不抛异常。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。
        目标字段 (str): 要提取的字段名（仅允许字母、数字、下划线）。
        时间字段 (str): 用于排序的时间字段名（仅允许字母、数字、下划线）。
        限制条数 (int | None): 最大返回数量；None 表示不限制。
        是否最新优先 (bool): True=最新优先（DESC），False=最旧优先（ASC）。

    Returns:
        list:
            - 成功：返回目标字段值列表。
            - 无数据或失败：返回空列表。
    """
    try:
        # 表名 / 字段名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return []
        if not re.fullmatch(r"[A-Za-z0-9_]+", 目标字段):
            return []
        if not re.fullmatch(r"[A-Za-z0-9_]+", 时间字段):
            return []

        # 预处理 LIMIT
        limit_value: Optional[int] = None
        if 限制条数 is not None:
            try:
                limit_value = int(限制条数)
            except (TypeError, ValueError):
                return []
            if limit_value <= 0:
                return []

        排序方向 = "DESC" if 是否最新优先 else "ASC"

        sql = (
            f"SELECT `{目标字段}` "
            f"FROM `{表名}` "
            f"WHERE `{时间字段}` IS NOT NULL "
            f"ORDER BY `{时间字段}` {排序方向}"
        )

        参数 = None
        if limit_value is not None:
            sql += " LIMIT %s"
            参数 = (limit_value,)

        with 连接对象.cursor() as 游标:
            if 参数 is not None:
                游标.execute(sql, 参数)
            else:
                游标.execute(sql)

            行列表 = 游标.fetchall() or []

        # 结果形态固定为 [(value,), ...]
        return [行[0] for 行 in 行列表]

    except Exception:
        return []
