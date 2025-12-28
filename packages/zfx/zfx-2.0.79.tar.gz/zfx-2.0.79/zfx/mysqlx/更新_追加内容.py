from __future__ import annotations

import re
from typing import Any


def 更新_追加内容(
    连接对象,
    表名: str,
    字段名: str,
    新内容: Any,
    条件: str,
) -> bool:
    """在指定表的某个字段中追加内容（不覆盖原有内容）。

    功能说明:
        - 使用 CONCAT + COALESCE 在原字段内容后追加新内容；
        - 若字段原值为 NULL，则视为空字符串；
        - 更新条件使用原生 SQL WHERE 子句；
        - 执行成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要更新的表名（仅允许字母、数字、下划线）。
        字段名 (str): 要追加内容的字段名（仅允许字母、数字、下划线）。
        新内容 (Any): 要追加的内容（会作为参数安全传入）。
        条件 (str): SQL WHERE 条件字符串（不包含 WHERE 关键字）。

    Returns:
        bool:
            - True  : 更新执行成功。
            - False : 更新失败或发生异常。

    Notes:
        - 本函数假定 条件 字符串来自可信代码；
        - 若条件来自外部输入，请自行做好安全控制；
        - 本函数会显式提交事务。
    """
    try:
        # 表名 / 字段名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return False
        if not re.fullmatch(r"[A-Za-z0-9_]+", 字段名):
            return False
        if not isinstance(条件, str) or not 条件.strip():
            return False

        sql = (
            f"UPDATE `{表名}` "
            f"SET `{字段名}` = CONCAT(COALESCE(`{字段名}`, ''), %s) "
            f"WHERE {条件}"
        )

        with 连接对象.cursor() as 游标:
            游标.execute(sql, (新内容,))

        连接对象.commit()
        return True

    except Exception:
        return False
