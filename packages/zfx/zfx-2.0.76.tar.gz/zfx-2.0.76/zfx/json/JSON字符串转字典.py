import json
from typing import Any, Optional, Union


def JSON字符串转字典(
    数据: Union[str, bytes, bytearray],
    *,
    失败返回空字典: bool = False
) -> Optional[Any]:
    """
    将标准 JSON 字符串解析为 Python 对象（通常为 dict 或 list）。

    功能说明：
        - 对 json.loads 的安全封装；
        - 支持 str / bytes / bytearray 输入；
        - 解析失败不会抛异常；
        - 可选择失败时返回 None 或 {}。

    Args:
        数据 (str | bytes | bytearray):
            JSON 字符串数据，例如 '{"a": 1}'。
        失败返回空字典 (bool):
            - False（默认）：失败返回 None
            - True：失败返回 {}

    Returns:
        Any | None:
            - 成功：返回解析后的 Python 对象（dict / list / 基础类型）
            - 失败：返回 None 或 {}
    """
    try:
        if isinstance(数据, (bytes, bytearray)):
            数据 = 数据.decode("utf-8")

        if not isinstance(数据, str):
            return {} if 失败返回空字典 else None

        return json.loads(数据)

    except Exception:
        return {} if 失败返回空字典 else None