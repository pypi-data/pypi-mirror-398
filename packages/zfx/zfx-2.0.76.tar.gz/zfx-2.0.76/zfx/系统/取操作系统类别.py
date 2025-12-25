import platform


def 取操作系统类别():
    """
    获取操作系统类别。

    返回:
        str: 当前操作系统类别，例如 "Windows 10"、"Windows 7"。如果获取失败，则返回 "未知版本"。

    使用示例:
        os_category = 取操作系统类别()
        print("操作系统类别:", os_category)
    """
    try:
        system = platform.system()
        version = platform.version()

        if "Windows" in system:
            # Windows 操作系统
            if "XP" in version:
                return "Windows XP"
            elif "2003" in version:
                return "Windows Server 2003"
            elif "Vista" in version:
                return "Windows Vista"
            elif "7" in version:
                return "Windows 7"
            elif "8.1" in version:
                return "Windows 8.1"
            elif "8" in version or "2012" in version:
                return "Windows 8/Windows Server 2012"
            elif "10" in version:
                return "Windows 10"
            else:
                return "未知版本"  # 未知版本
        else:
            return "非 Windows 系统"  # 非 Windows 系统，返回未知版本
    except Exception:
        return "未知版本"