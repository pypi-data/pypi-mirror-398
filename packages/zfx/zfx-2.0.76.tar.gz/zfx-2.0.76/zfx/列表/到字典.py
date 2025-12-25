from typing import Any, Dict, List


def 到字典(
    键名: str,
    值列表: List[Any]
) -> Dict[str, List[Any]]:
    """
    将给定列表作为值，按指定键名封装为字典。

    功能说明：
        - 接收一个键名和一个列表；
        - 返回结构为 {键名: 列表} 的字典；
        - 若键名不是字符串，或值不是列表，返回空字典；
        - 不修改原列表；
        - 不抛异常、不打印日志，适合作为底层通用工具函数。

    Args:
        键名 (str): 字典的键名。
        值列表 (list): 作为字典值的列表。

    Returns:
        dict:
            - 成功：{键名: 值列表}
            - 失败：{}
    """
    try:
        if not isinstance(键名, str):
            return {}

        if not isinstance(值列表, list):
            return {}

        return {键名: 值列表}
    except Exception:
        return {}