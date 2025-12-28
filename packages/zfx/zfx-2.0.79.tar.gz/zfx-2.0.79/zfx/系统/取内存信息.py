import platform
import os

def 取内存信息() -> dict:
    """
    获取当前系统的内存使用信息（静默执行版）。

    功能说明：
        - 支持 Windows、Linux、macOS 系统。
        - 自动检测系统平台并调用相应方法获取内存总量与可用量。
        - 返回结果以字典形式包含总量、已用、空闲及使用率（单位：MB、%）。
        - 函数为静默模式：不打印任何提示或错误，不抛出异常。
        - 若执行失败或权限不足，返回空字典。

    Returns:
        dict:
            {
                "总内存_MB": float,    # 系统总内存（MB）
                "已用内存_MB": float,  # 已使用内存（MB）
                "可用内存_MB": float,  # 剩余可用内存（MB）
                "使用率_%": float       # 内存使用百分比
            }
            若获取失败返回 {}。

    Notes:
        - Windows:
            读取 `os.sysconf('SC_PAGE_SIZE')` 与 `os.sysconf('SC_PHYS_PAGES')` 无效，
            因此使用 `ctypes.windll.kernel32.GlobalMemoryStatusEx` 获取。
        - Linux/macOS:
            读取 `/proc/meminfo` 或使用 `os.sysconf` 获取物理内存与空闲页。
        - 单位统一转换为 MB（保留两位小数）。

    Example:
        信息 = 取内存信息()
        if 信息:
            print(f"总内存: {信息['总内存_MB']} MB | 使用率: {信息['使用率_%']}%")
    """
    try:
        系统 = platform.system().lower()

        # Windows 系统
        if 系统 == "windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return {}

            总 = stat.ullTotalPhys / (1024 ** 2)
            可用 = stat.ullAvailPhys / (1024 ** 2)
            已用 = 总 - 可用
            使用率 = round((已用 / 总) * 100, 2)

            return {
                "总内存_MB": round(总, 2),
                "已用内存_MB": round(已用, 2),
                "可用内存_MB": round(可用, 2),
                "使用率_%": 使用率
            }

        # Linux 或 macOS
        elif 系统 in ("linux", "darwin"):
            try:
                if os.path.exists("/proc/meminfo"):
                    with open("/proc/meminfo", "r", encoding="utf-8") as f:
                        内容 = f.read()
                    数据 = {}
                    for 行 in 内容.splitlines():
                        if ":" in 行:
                            键, 值 = 行.split(":", 1)
                            数据[键.strip()] = int(值.strip().split()[0])
                    总 = 数据.get("MemTotal", 0) / 1024
                    可用 = 数据.get("MemAvailable", 数据.get("MemFree", 0)) / 1024
                    已用 = 总 - 可用
                    使用率 = round((已用 / 总) * 100, 2) if 总 else 0.0
                else:
                    页大小 = os.sysconf("SC_PAGE_SIZE") / 1024  # KB
                    总页数 = os.sysconf("SC_PHYS_PAGES")
                    可用页 = os.sysconf("SC_AVPHYS_PAGES")
                    总 = (总页数 * 页大小) / 1024
                    可用 = (可用页 * 页大小) / 1024
                    已用 = 总 - 可用
                    使用率 = round((已用 / 总) * 100, 2)
                return {
                    "总内存_MB": round(总, 2),
                    "已用内存_MB": round(已用, 2),
                    "可用内存_MB": round(可用, 2),
                    "使用率_%": 使用率
                }
            except Exception:
                return {}

        else:
            return {}

    except Exception:
        return {}
