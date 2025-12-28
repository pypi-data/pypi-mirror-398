from datetime import datetime

def ISO格式转标准时间(时间字符串: str) -> str | None:
    """
    将 ISO 8601 时间字符串转换为标准的 MySQL 时间格式（YYYY-MM-DD HH:MM:SS）。

    功能说明：
        本函数用于解析常见的 ISO 格式时间字符串（如 "2025-11-13T06:50:00Z"、
        "2025-11-13T06:50:00+00:00" 等），并返回标准格式。
        若解析失败，则返回 None 而非抛出异常，以方便在批量处理中使用。

    Args:
        时间字符串 (str): ISO 格式的时间字符串。

    Returns:
        str | None: 转换后的标准时间字符串（格式为 "YYYY-MM-DD HH:MM:SS"）；
                    若解析失败则返回 None。

    Example:
        ISO格式转标准时间("2025-11-13T06:50:00Z")
        → "2025-11-13 06:50:00"
    """
    try:
        dt = datetime.fromisoformat(时间字符串.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
