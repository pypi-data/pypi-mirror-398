from datetime import datetime


def 取当前日期() -> str:
    """
    获取当前系统日期（仅年月日），格式固定为 "YYYY-MM-DD"。

    功能说明：
        - 适用于记录日志、生成文件名、数据库日期字段等场景。
        - 内部基于 datetime.now()，受系统时区影响。

    Returns:
        str: 当前日期字符串，格式为 "2025-11-12"。
    """
    return datetime.now().strftime("%Y-%m-%d")