from __future__ import annotations

import re


def 更新_清空数据表(
    连接对象,
    表名: str,
) -> bool:
    """清空指定 MySQL 表中的所有数据（TRUNCATE TABLE）。

    功能说明:
        - 使用 TRUNCATE TABLE 语句清空整张表的数据；
        - 会重置自增主键（AUTO_INCREMENT）；
        - 不可回滚（在大多数 MySQL 配置下）；
        - 执行成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放。

    ⚠ 风险提示:
        - 本函数会永久删除整张表的所有数据；
        - 调用前请务必确认业务逻辑无误。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要清空的表名（仅允许字母、数字、下划线）。

    Returns:
        bool:
            - True  : 表清空成功。
            - False : 操作失败或发生异常。
    """
    try:
        # 表名安全校验
        if not re.fullmatch(r"[A-Za-z0-9_]+", 表名):
            return False

        sql = f"TRUNCATE TABLE `{表名}`"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)

        # TRUNCATE 在 MySQL 中通常会隐式提交，但这里显式 commit 保持语义统一
        连接对象.commit()
        return True

    except Exception:
        return False
