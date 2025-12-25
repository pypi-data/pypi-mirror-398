import os


def 取系统桌面目录():
    """
    获取当前系统的桌面目录路径。

    返回值：
        - 桌面目录路径：返回当前用户的桌面路径。如果获取失败，则返回 None。

    使用示例（可以复制并直接修改）：
        桌面目录 = zfx_dir.取系统桌面目录()

        # 打印桌面目录路径
        print("系统桌面目录:", 桌面目录)
    """
    try:
        # 判断操作系统类型
        if os.name == 'nt':  # Windows 系统
            桌面目录 = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        else:  # macOS 或 Linux 系统
            桌面目录 = os.path.join(os.path.expanduser('~'), 'Desktop')

        # 检查桌面目录是否存在
        if os.path.exists(桌面目录):
            return 桌面目录
        else:
            return None
    except Exception:
        return None