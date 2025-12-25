import shutil
import os


def 复制(被复制文件名, 复制到文件名, 是否覆盖=False):
    """
    复制文件。

    参数：
    被复制文件名（str）：要复制的文件名。
    复制到文件名（str）：复制后的文件名。
    是否覆盖（bool）：可选参数，指示是否覆盖已存在的文件。默认为 False，表示不覆盖。

    返回：
    bool：如果复制成功，则返回 True，否则返回 False。

    # 示例用法
    zfxtest.文件_复制("亚马逊账户.txt", "亚马逊账户2.txt", 是否覆盖=False)
    """
    try:
        # 如果不允许覆盖且目标文件已存在，则直接返回 False
        if not 是否覆盖 and os.path.exists(复制到文件名):
            return False

        # 复制文件
        shutil.copy2(被复制文件名, 复制到文件名)
        return True
    except Exception:
        return False