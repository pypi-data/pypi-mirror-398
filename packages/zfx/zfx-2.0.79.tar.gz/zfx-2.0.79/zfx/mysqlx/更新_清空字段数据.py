from __future__ import annotations

import re


def 更新_清空字段数据(
    连接对象,
    表名: str,
    字段名: str,
    *,
    置为NULL: bool = False,
) -> bool:
    """清空指定表中某个字段的所有数据（全表更新）。

    功能说明:
        - 对整张表执行 UPDATE，将指定字段统一设置为空字符串 '' 或 NULL；
        - 默认置为空字符串 ''（保持旧版本行为）；
        - 若 置为NULL=True，则把该字段全部设为 NULL；
        - 执行成功返回 True，失败返回 False；
        - 游标在函数内部创建并自动释放。

    ⚠ 风险提示:
        - 本函数不包含 WHERE 条件，会修改整张表该字段的所有行；
        - 请确保调用前已确认业务逻辑正确。

    Args:
        连接对象: 已建立的 MySQL 数据库连接对象。
        表名 (str): 要更新的表名（仅允许字母、数字、下划线）。
        字段名 (str): 要清空的字段名（仅允许字母、数字、下划线）。
        置为NULL (bool): True=全部置为 NULL；False=全部置为 ''。

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

        set_expr = "NULL" if 置为NULL else "''"
        sql = f"UPDATE `{表名}` SET `{字段名}` = {set_expr}"

        with 连接对象.cursor() as 游标:
            游标.execute(sql)

        连接对象.commit()
        return True

    except Exception:
        return False
