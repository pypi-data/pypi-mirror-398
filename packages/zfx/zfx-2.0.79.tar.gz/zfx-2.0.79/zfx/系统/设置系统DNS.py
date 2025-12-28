import platform
import subprocess


def 设置系统DNS(适配器名: str, 主DNS: str, 备DNS: str = None) -> bool:
    """
    修改系统指定网络适配器的 DNS 设置（静默执行版）。

    功能说明：
        - 支持在 Windows、Linux、macOS 系统上修改 DNS 服务器地址。
        - 内部自动识别操作系统并执行相应命令：
            * Windows：调用 netsh 修改指定适配器的 DNS。
            * Linux：直接覆盖 /etc/resolv.conf 文件。
            * macOS：调用 networksetup 修改网络服务的 DNS。
        - 该函数为“静默模式”：不打印任何提示或错误，不抛出异常。
        - 若执行成功返回 True，任何失败或异常均返回 False。
        - 所有系统均需管理员 / root 权限才能生效。

    Args:
        适配器名 (str): 网络适配器或网络服务名称。
            - Windows 示例："以太网"、"Wi-Fi"。
            - macOS 示例："Wi-Fi"、"Thunderbolt Bridge"。
            - Linux 下该参数不会被使用，可传 None。
        主DNS (str): 主 DNS 服务器地址，例如 "8.8.8.8"。
        备DNS (str, optional): 备 DNS 服务器地址，例如 "8.8.4.4"。默认值为 None。

    Returns:
        bool:
            - True：DNS 修改成功；
            - False：执行过程中发生错误或权限不足。

    Notes:
        - Windows 环境：
            调用系统命令：
                netsh interface ip set dns name=<适配器名> static <主DNS>
                netsh interface ip add dns name=<适配器名> <备DNS> index=2
            修改完成后自动执行 ipconfig /flushdns 刷新缓存。
        - Linux 环境：
            直接重写 /etc/resolv.conf 内容为：
                nameserver 主DNS
                nameserver 备DNS (可选)
            若系统使用 systemd-resolved，会尝试重启该服务。
        - macOS 环境：
            调用命令：
                networksetup -setdnsservers <适配器名> <主DNS> [备DNS]
        - 所有操作均需要管理员权限；若无权限，函数不会报错，仅返回 False。

        推荐公共 DNS（稳定且速度较快）：
            - Google DNS：
                主：8.8.8.8
                备：8.8.4.4
            - Cloudflare DNS：
                主：1.1.1.1
                备：1.0.0.1
            - OpenDNS（Cisco）：
                主：208.67.222.222
                备：208.67.220.220
            - Quad9 安全 DNS：
                主：9.9.9.9
                备：149.112.112.112
            - 阿里 DNS（适合中国大陆）：
                主：223.5.5.5
                备：223.6.6.6
            - 腾讯 DNSPod：
                主：119.29.29.29
                备：182.254.116.116
            - 114DNS（中国大陆通用）：
                主：114.114.114.114
                备：114.114.115.115

    Example:
        结果 = 设置系统DNS("以太网", "8.8.8.8", "114.114.114.114")
        if 结果:
            print("DNS修改成功")
        else:
            print("DNS修改失败")
    """
    try:
        系统 = platform.system().lower()

        if 系统 == "windows":
            # 主 DNS
            r1 = subprocess.run(
                ["netsh", "interface", "ip", "set", "dns", f"name={适配器名}", "static", 主DNS],
                check=True, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            # 备 DNS（可选）
            if 备DNS:
                subprocess.run(
                    ["netsh", "interface", "ip", "add", "dns", f"name={适配器名}", 备DNS, "index=2"],
                    check=False, shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            # 刷新缓存
            subprocess.run(
                ["ipconfig", "/flushdns"],
                check=False, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return r1.returncode == 0

        elif 系统 == "linux":
            内容 = f"nameserver {主DNS}\n" + (f"nameserver {备DNS}\n" if 备DNS else "")
            with open("/etc/resolv.conf", "w", encoding="utf-8") as f:
                f.write(内容)
            subprocess.run(
                ["systemctl", "restart", "systemd-resolved"],
                check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True

        elif 系统 == "darwin":
            命令 = ["networksetup", "-setdnsservers", 适配器名, 主DNS] + ([备DNS] if 备DNS else [])
            r = subprocess.run(命令, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return r.returncode == 0

        else:
            return False

    except Exception:
        return False