import json
from typing import Any, Dict


def 更新_JSON字段(
    连接对象,
    游标对象,
    表名: str,
    字段名: str,
    JSON数据: Dict[str, Any],
    条件: str,
) -> bool:
    """
    在 MySQL 5.7 环境下通用更新 JSON 字段：以“顶层键整体覆盖”的方式合入 JSON数据。
    命中行即视为成功（不再依赖 rowcount 是否>0）。

    功能说明:
        - 兼容 MySQL 5.7：使用 JSON_SET 一次性写入多个路径；
        - 将目标 JSON 列视作对象（为 NULL 则当作 {}）；
        - 对 JSON数据 中的每个顶层键 k，执行：$.\"k\" = 值（整体覆盖）；
        - 更新成功与否以“是否命中 WHERE 条件”为准：命中即 True，未命中 False。

    Args:
        连接对象: 数据库连接对象（需支持 commit/rollback）。
        游标对象: 数据库游标对象。
        表名 (str): 目标表名。
        字段名 (str): 目标 JSON 字段名。
        JSON数据 (dict): 需要写入的“顶层键 → 值”的字典；同名键将被覆盖更新或新增。
        条件 (str): WHERE 条件（不含 “WHERE”），例如 "id=123" 或 "productId='9NV123'”。

    Returns:
        bool: True 表示命中行且 UPDATE 执行成功；False 表示未命中或异常。

    使用示例:
        示例一：更新单个
        JSON数据 = {"US": {"ListPrice": 9.99,"MSRP": 19.99,"CurrencyCode": "USD"}}
        更新JSON字段(连接对象,游标对象,表名="example_table",字段名="price",JSON数据=JSON数据,条件="id=1")

        示例二：一次更新多个顶层键
        JSON数据 = {"JP": {"ListPrice": 980, "CurrencyCode": "JPY"},"DE": {"ListPrice": 8.99, "CurrencyCode": "EUR"}}
        更新JSON字段(连接对象,游标对象,表名="example_table",字段名="price",JSON数据=JSON数据,条件="id=1")
    语义与边界:
        - 合并语义为“顶层覆盖”：仅覆盖 JSON数据 中出现的顶层键；不做深度递归合并。
        - 若需深度合并，请在调用前自行构造目标值（例如先读出旧 JSON，在 Python 内合并后整体写入该键）。
        - 条件为原样拼接版，务必确保来源可控；生产中建议封装一个带参数化条件的变体以防注入。
    """
    try:
        if not isinstance(JSON数据, dict) or not JSON数据:
            return False

        # 1) 先判断是否命中行（避免 rowcount=0 造成“成功却返回 False”）
        sql_exist = f"SELECT COUNT(1) FROM `{表名}` WHERE {条件} LIMIT 1"
        游标对象.execute(sql_exist)
        命中 = 游标对象.fetchone()
        命中行数 = (list(命中.values())[0] if isinstance(命中, dict) else 命中[0]) if 命中 else 0
        if 命中行数 <= 0:
            return False  # 条件未命中，不做 UPDATE

        # 2) 组装 JSON_SET 变参: (path1, val1, path2, val2, ...)
        路径与值占位 = []
        参数 = []
        for 顶层键, 值 in JSON数据.items():
            路径与值占位.append("%s")
            路径与值占位.append("CAST(%s AS JSON)")
            路径 = f'$.\"{str(顶层键).strip()}\"'
            参数.append(路径)
            参数.append(json.dumps(值, ensure_ascii=False, separators=(",", ":")))

        set子句 = (
            f"`{字段名}` = JSON_SET(COALESCE(`{字段名}`, JSON_OBJECT()), "
            + ", ".join(路径与值占位)
            + ")"
        )
        SQL = f"UPDATE `{表名}` SET {set子句} WHERE {条件}"

        游标对象.execute(SQL, 参数)
        连接对象.commit()
        return True

    except Exception:
        try:
            连接对象.rollback()
        except Exception:
            pass
        return False
