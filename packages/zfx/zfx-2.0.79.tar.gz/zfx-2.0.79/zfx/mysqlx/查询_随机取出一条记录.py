from __future__ import annotations

import random
import re
from typing import Any, Optional, Tuple


def 查询_随机取出一条记录(
    连接对象,
    表名: str,
) -> Optional[Tuple[Any, ...]]:
    """从指定 MySQL 表中随机取出一条记录。

    功能说明:
        - 从表中随机选取一条记录并返回；
        - 若表为空、查询失败或发生异常，返回 None；
        - 游标在函数内部创建并自动释放；
        - 不打印、不抛异常，适合作为底层工具函数。

    Args:
        连接对象: 已建立的 MySQL 连接对象。
        表名 (str): 要查询的表名（仅允许字母、数字、下划线）。

    Returns:
        tuple | None:
            - 成功：返回一条记录（tuple）。
            - 失败或无数据：返回 None。
    """
    try:
        # 简单校验表名，防止 SQL 注入
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return None

        with 连接对象.cursor() as 游标:
            # 1. 获取总记录数
            游标.execute(f"SELECT COUNT(*) FROM `{表名}`")
            总记录数 = 游标.fetchone()[0]

            if not 总记录数 or 总记录数 <= 0:
                return None

            # 2. 生成随机偏移量
            随机偏移量 = random.randint(0, 总记录数 - 1)

            # 3. 按偏移量取一条
            游标.execute(
                f"SELECT * FROM `{表名}` LIMIT 1 OFFSET %s",
                (随机偏移量,),
            )
            return 游标.fetchone()

    except Exception:
        return None
