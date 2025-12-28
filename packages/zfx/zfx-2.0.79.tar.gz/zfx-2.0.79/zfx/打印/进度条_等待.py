import sys
import time


def 进度条_等待(总秒数: int, 长度: int = 40) -> bool:
    """
    在指定时间内持续显示进度条，用作可视化等待工具。
    可替代 time.sleep，使等待过程可视化。

    功能说明：
        - 每秒刷新一次进度条，展示百分比、已等待时间、剩余时间；
        - 自动显示总等待时长，例如“总计 3600s”；
        - 适用于轮询、限频等待、定时任务等场景；
        - 不抛异常，是底层工具函数的安全实现。

    Args:
        总秒数 (int): 需要等待的总时长（秒）。
        长度 (int): 进度条长度（字符数），默认 40。

    Returns:
        bool:
            True：正常完成；
            False：发生异常。

    Notes:
        - 每秒刷新一次；
        - 若总秒数 <= 0，将直接返回 True；
        - 使用 sys.stdout.write 实现原地刷新。
    """
    try:
        总秒数 = int(总秒数)
        if 总秒数 <= 0:
            return True

        for 已等待 in range(总秒数 + 1):
            百分比 = 已等待 / 总秒数
            完成长度 = int(长度 * 百分比)
            进度 = "█" * 完成长度 + "-" * (长度 - 完成长度)

            剩余 = 总秒数 - 已等待

            sys.stdout.write(
                f"\r|{进度}| {百分比:.2%} | 已等待 {已等待}s | 剩余 {剩余}s | 总计 {总秒数}s"
            )
            sys.stdout.flush()

            if 已等待 < 总秒数:
                time.sleep(1)

        print()
        return True

    except Exception:
        return False