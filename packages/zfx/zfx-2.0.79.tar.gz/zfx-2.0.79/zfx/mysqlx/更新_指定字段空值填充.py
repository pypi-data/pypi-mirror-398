from __future__ import annotations

import re
from typing import Any


def 更新_指定字段空值填充(
    连接对象,
    表名: str,
    字段名: str,
    填充数据: Any,
) -> bool:
    """将指定表中某字段的空值（NULL 或空字符串）统一填充为给定值。

    功能说明:
        - 更新条件：字段 IS NULL 或 字段 = ''；
        - 将符合条件的记录统一填充为指定值；
        - 使用参数化查询，避免 SQL 注入；
        - 执行成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放。

    ⚠ 风险提示:
        - 本函数不包含额外 WHERE 条件，会影响整张表中该字段的空值记录；
        - 请确保调用前已确认业务逻辑。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要更新的表名（仅允许字母、数字、下划线）。
        字段名 (str): 要填充空值的字段名（仅允许字母、数字、下划线）。
        填充数据 (Any): 用于填充的值（通过参数化安全传入）。

    Returns:
        bool:
            - True  : 更新执行成功。
            - False : 更新失败或发生异常。
    """
    try:
        # 表名 / 字段名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return False
        if not re.fullmatch(r"[A-Za-z0-9_]+", 字段名):
            return False

        sql = (
            f"UPDATE `{表名}` "
            f"SET `{字段名}` = %s "
            f"WHERE `{字段名}` IS NULL OR `{字段名}` = ''"
        )

        with 连接对象.cursor() as 游标:
            游标.execute(sql, (填充数据,))

        连接对象.commit()
        return True

    except Exception:
        return False