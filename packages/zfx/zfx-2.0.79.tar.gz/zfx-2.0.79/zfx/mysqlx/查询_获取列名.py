from __future__ import annotations

import re
from typing import List


def 查询_获取列名(
    连接对象,
    表名: str,
) -> List[str]:
    """获取指定 MySQL 表的所有列名。

    功能说明:
        - 通过 DESCRIBE 语句获取表的字段列表；
        - 成功返回列名字符串列表；
        - 查询失败、表不存在或异常时返回空列表；
        - 游标在函数内部创建并自动释放。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。

    Returns:
        list[str]:
            - 成功：返回列名列表，例如 ["id", "name", "created_at"]。
            - 失败：返回空列表。
    """
    try:
        # 表名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return []

        with 连接对象.cursor() as 游标:
            游标.execute(f"DESCRIBE `{表名}`")
            结果 = 游标.fetchall() or []

        # DESCRIBE 第一列固定为字段名
        return [行[0] for 行 in 结果]

    except Exception:
        return []
