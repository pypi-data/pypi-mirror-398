from datetime import datetime
from typing import Optional


def 打印系统时间(
    前缀: str = "",
    格式: Optional[str] = "%Y-%m-%d %H:%M:%S",
) -> bool:
    """
    打印当前系统时间，可自定义前缀与时间格式。

    功能说明：
        - 获取当前系统时间并按指定格式打印；
        - 支持添加前缀文本，用于标注任务执行阶段或日志信息；
        - 若格式字符串非法，将自动降级为默认格式 "%Y-%m-%d %H:%M:%S"；
        - 本函数不抛异常，是底层打印工具函数的安全实现。

    Args:
        前缀 (str): 打印在时间前面的文本内容，默认空字符串。
        格式 (str | None): 时间格式化字符串，遵循 datetime.strftime 规则。
                           若为 None 或格式无效，将使用默认格式。

    Returns:
        bool:
            True：打印成功；
            False：出现异常。

    Notes:
        - 若前缀不为空，会自动在前缀与时间之间加入一个空格；
        - 常见格式示例：
            "%H:%M:%S"
            "%Y-%m-%d"
            "%Y-%m-%d %H:%M:%S"
        - datetime.now() 获取本地系统时间。
    """
    try:
        时间对象 = datetime.now()

        # 优先尝试用户格式，不行则回退默认格式
        try:
            时间文本 = 时间对象.strftime(格式) if 格式 else 时间对象.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            时间文本 = 时间对象.strftime("%Y-%m-%d %H:%M:%S")

        # 处理前缀
        输出 = f"{前缀} {时间文本}" if 前缀 else 时间文本

        print(输出)
        return True

    except Exception:
        return False