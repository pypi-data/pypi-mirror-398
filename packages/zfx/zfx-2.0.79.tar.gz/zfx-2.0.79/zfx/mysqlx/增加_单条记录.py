from __future__ import annotations

import re
from typing import Any, Mapping


def 增加_单条记录(
    连接对象,
    表名: str,
    数据字典: Mapping[str, Any],
) -> bool:
    """向指定 MySQL 表中插入一条记录。

    功能说明:
        - 根据 数据字典 动态生成 INSERT 语句；
        - 所有值使用参数化传递，避免 SQL 注入；
        - 执行成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要插入记录的表名（仅允许字母、数字、下划线）。
        数据字典 (Mapping[str, Any]):
            字段名到值的映射，例如 {"name": "Tom", "age": 18}。

    Returns:
        bool:
            - True  : 插入成功。
            - False : 参数非法或插入失败。

    Notes:
        - 数据字典不能为空；
        - 字段名属于 SQL 标识符，无法参数化，因此会进行白名单校验；
        - 本函数会显式提交事务。
    """
    try:
        # 基本校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return False
        if not 数据字典:
            return False

        # 校验字段名
        for 字段名 in 数据字典.keys():
            if not isinstance(字段名, str) or not re.fullmatch(r"[A-Za-z0-9_]+", 字段名):
                return False

        字段列表 = ", ".join(f"`{字段}`" for 字段 in 数据字典.keys())
        占位符 = ", ".join(["%s"] * len(数据字典))

        sql = f"INSERT INTO `{表名}` ({字段列表}) VALUES ({占位符})"

        with 连接对象.cursor() as 游标:
            游标.execute(sql, tuple(数据字典.values()))

        连接对象.commit()
        return True

    except Exception:
        return False
