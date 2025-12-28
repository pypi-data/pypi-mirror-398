from __future__ import annotations

import re
from typing import Any, Dict, List

from pymysql.cursors import DictCursor


def 查询_表结构(
    连接对象,
    表名: str,
) -> List[Dict[str, Any]]:
    """查询指定 MySQL 表的结构信息（字段定义）。

    功能说明:
        - 执行 DESCRIBE `表名` 获取字段结构；
        - 返回字段名称、类型、是否允许 NULL、键类型、默认值、扩展信息等；
        - 失败返回空列表，不抛异常、不打印。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。

    Returns:
        list[dict]:
            成功时返回字段结构列表，每项包含：
            - Field
            - Type
            - Null
            - Key
            - Default
            - Extra

            异常或表不存在时返回空列表。
    """
    try:
        # 表名安全校验，防止注入
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return []

        sql = f"DESCRIBE `{表名}`"

        # 临时使用 DictCursor，避免手工映射下标
        with 连接对象.cursor(DictCursor) as 游标:
            游标.execute(sql)
            结果 = 游标.fetchall() or []

        # 统一只返回我们关心的键，避免不同驱动/版本字段差异导致上层崩
        输出: List[Dict[str, Any]] = []
        for 行 in 结果:
            输出.append(
                {
                    "Field": 行.get("Field"),
                    "Type": 行.get("Type"),
                    "Null": 行.get("Null"),
                    "Key": 行.get("Key"),
                    "Default": 行.get("Default"),
                    "Extra": 行.get("Extra"),
                }
            )
        return 输出

    except Exception:
        return []