from typing import Any, List, Optional


def 查询_字段值_按时间排序(
    连接对象,
    游标对象,
    表名: str,
    目标字段: str,
    时间字段: str,
    *,
    限制条数: Optional[int] = None,
    是否最新优先: bool = True,
) -> List[Any]:
    """
    按时间字段排序，批量取出目标字段的值。

    功能说明:
        - 根据指定的时间字段进行排序，从表中取出目标字段的值列表。
        - 支持“取最新的若干条”或“取最久远的若干条”两种模式：
            * 是否最新优先=True  → 按时间字段 DESC 排序（最新在前）。
            * 是否最新优先=False → 按时间字段 ASC 排序（最旧在前）。
        - 可通过限制条数控制最大返回数量，例如只取前 100 条。
        - 若限制条数为 None，则不加 LIMIT，返回所有符合条件的记录。
        - 为避免时间为空干扰排序，默认只统计时间字段非 NULL 的记录。
        - 异常安全：任何异常都会返回空列表，不抛出错误。

    Args:
        连接对象: 已连接好的 MySQL 连接对象（本函数不主动提交，仅保留接口统一性）。
        游标对象: 用于执行 SQL 的游标对象。
        表名 (str): 要查询的表名。
        目标字段 (str): 需要取出的字段名，例如 "id"、"product_url"。
        时间字段 (str): 用于排序的时间字段名，例如 "update_time"、"created_at"。
        限制条数 (int | None, optional): 最大返回条数；为 None 时不限制。
        是否最新优先 (bool, optional): True 表示按时间倒序（最新优先），
            False 表示按时间正序（最久优先）。

    Returns:
        list: 一维列表，元素为目标字段的值；
            - 查询正常但无符合条件记录时，返回空列表；
            - 出现任何异常时，也返回空列表。
    """
    # 预处理 LIMIT 参数
    limit_value: Optional[int] = None
    if 限制条数 is not None:
        try:
            limit_value = int(限制条数)
        except (TypeError, ValueError):
            # 限制条数非法，直接返回空
            return []
        if limit_value <= 0:
            # 0 或负数没有意义，直接返回空
            return []

    排序方向 = "DESC" if 是否最新优先 else "ASC"

    # 只取时间字段非 NULL 的记录，避免 NULL 干扰排序含义
    sql = (
        f"SELECT `{目标字段}` "
        f"FROM `{表名}` "
        f"WHERE `{时间字段}` IS NOT NULL "
        f"ORDER BY `{时间字段}` {排序方向}"
    )

    参数 = None
    if limit_value is not None:
        sql += " LIMIT %s"
        参数 = (limit_value,)

    try:
        if 参数 is not None:
            游标对象.execute(sql, 参数)
        else:
            游标对象.execute(sql)

        行列表 = 游标对象.fetchall()
        结果列表: List[Any] = []

        for 行 in 行列表:
            try:
                if isinstance(行, tuple):
                    结果列表.append(行[0] if len(行) > 0 else None)
                elif isinstance(行, dict):
                    值列表 = list(行.values())
                    结果列表.append(值列表[0] if 值列表 else None)
                else:
                    # 兜底情况：未知类型，尝试用索引取第一个
                    try:
                        结果列表.append(行[0])  # type: ignore[index]
                    except Exception:
                        continue
            except Exception:
                # 单行异常直接忽略，不影响整体
                continue

        return 结果列表
    except Exception:
        return []