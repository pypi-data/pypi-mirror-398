from __future__ import annotations

import re


def 更新_置字段所有数据为Null(
    连接对象,
    表名: str,
    字段名: str,
) -> bool:
    """将指定表中某个字段的所有数据置为 NULL（全表更新）。

    功能说明:
        - 对整张表执行 UPDATE，将指定字段的值全部设为 NULL；
        - 不包含 WHERE 条件，影响该字段的所有行；
        - 更新成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放。

    ⚠ 风险提示:
        - 本函数会无条件修改整张表的数据；
        - 请确保调用前已确认业务逻辑正确。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要更新的表名（仅允许字母、数字、下划线）。
        字段名 (str): 要置为 NULL 的字段名（仅允许字母、数字、下划线）。

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

        sql = f"UPDATE `{表名}` SET `{字段名}` = NULL"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)

        连接对象.commit()
        return True

    except Exception:
        return False