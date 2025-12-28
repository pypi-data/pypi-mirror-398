from __future__ import annotations

import re
from typing import Any, Mapping


def 更新_SQL语句条件(
    连接对象,
    表名: str,
    值字典: Mapping[str, Any],
    条件: str,
) -> bool:
    """根据值字典与 WHERE 条件更新指定表的数据。

    功能说明:
        - 将 值字典 转换为 UPDATE 的 SET 子句（参数化 %s）；
        - 条件为原生 SQL WHERE 字符串（不包含 WHERE 关键字）；
        - 执行成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放，并显式 commit。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要更新的表名（仅允许字母、数字、下划线）。
        值字典 (Mapping[str, Any]): 需要更新的列和值映射，例如 {"name": "John", "age": 20}。
        条件 (str): WHERE 条件字符串，例如 "id = 1"。

    Returns:
        bool:
            - True  : 更新执行成功。
            - False : 参数非法或更新失败。

    Notes:
        - 本函数假定 条件 字符串来自可信代码；若条件来自外部输入，请自行做安全控制。
        - 表名与列名属于 SQL 标识符，无法参数化，因此本函数会进行白名单校验。
    """
    try:
        # 基本校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return False
        if not isinstance(条件, str) or not 条件.strip():
            return False
        if not 值字典:
            return False

        # 校验字段名
        for 列名 in 值字典.keys():
            if not isinstance(列名, str) or not re.fullmatch(r"[A-Za-z0-9_]+", 列名):
                return False

        # 生成 SET 子句：`col`=%s, `col2`=%s ...
        set_clause = ", ".join([f"`{列名}` = %s" for 列名 in 值字典.keys()])

        sql = f"UPDATE `{表名}` SET {set_clause} WHERE {条件}"

        with 连接对象.cursor() as 游标:
            游标.execute(sql, tuple(值字典.values()))

        连接对象.commit()
        return True

    except Exception:
        return False
