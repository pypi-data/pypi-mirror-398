import random


def 生成随机UA(
    浏览器: str | None = None,
    系统: str | None = None
) -> str:
    """
    生成一个随机的浏览器 User-Agent 字符串。

    功能说明：
        用于在爬虫或 HTTP 请求中伪装不同浏览器环境。
        可指定浏览器类型和操作系统；若不指定则随机选择。
        生成结果尽量贴近真实浏览器 UA 格式。

    参数：
        浏览器 (str | None):
            可选的浏览器名称。
            支持值：'chrome'、'firefox'、'safari'、'edge'、'opera'。
            默认为 None，表示随机选择一种浏览器。
        系统 (str | None):
            可选的操作系统名称。
            支持值：'windows'、'macos'、'linux'、'android'、'ios'。
            默认为 None，表示随机选择一种系统。

    返回：
        str:
            一个随机生成的 User-Agent 字符串。

    使用示例：
        示例一：生成任意随机 UA
            ua = 生成随机UA()
            print(ua)

        示例二：生成 Chrome 浏览器 UA
            ua = 生成随机UA(浏览器="chrome")
            print(ua)

        示例三：生成 macOS + Safari 的 UA
            ua = 生成随机UA(浏览器="safari", 系统="macos")
            print(ua)

    说明：
        1. 所有版本号均随机生成但保持合理区间。
        2. 若需固定 UA，可自行缓存生成结果。
        3. 本函数仅生成常见现代浏览器标识。
    """
    浏览器列表 = ["chrome", "firefox", "safari", "edge", "opera"]
    系统列表 = ["windows", "macos", "linux", "android", "ios"]

    if 浏览器 not in 浏览器列表:
        浏览器 = random.choice(浏览器列表)
    if 系统 not in 系统列表:
        系统 = random.choice(系统列表)

    # 随机版本生成
    chrome_ver = f"{random.randint(120, 134)}.0.{random.randint(1000, 5999)}.{random.randint(50, 200)}"
    firefox_ver = f"{random.randint(110, 128)}.0"
    safari_ver = f"{random.randint(600, 620)}.{random.randint(1, 50)}.{random.randint(1, 10)}"
    osx_ver = f"{random.randint(10, 14)}_{random.randint(0, 6)}"
    ios_ver = f"{random.randint(14, 17)}_{random.randint(0, 6)}"

    # 系统标识块
    if 系统 == "windows":
        sys_block = "Windows NT 10.0; Win64; x64"
    elif 系统 == "macos":
        sys_block = f"Macintosh; Intel Mac OS X {osx_ver}"
    elif 系统 == "linux":
        sys_block = "X11; Linux x86_64"
    elif 系统 == "android":
        sys_block = f"Linux; Android {random.randint(8, 14)}; Mobile"
    elif 系统 == "ios":
        sys_block = f"iPhone; CPU iPhone OS {ios_ver} like Mac OS X"
    else:
        sys_block = "Windows NT 10.0; Win64; x64"

    # 构造UA
    if 浏览器 == "chrome":
        ua = f"Mozilla/5.0 ({sys_block}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"
    elif 浏览器 == "firefox":
        ua = f"Mozilla/5.0 ({sys_block}; rv:{firefox_ver}) Gecko/20100101 Firefox/{firefox_ver}"
    elif 浏览器 == "safari":
        ua = f"Mozilla/5.0 ({sys_block}) AppleWebKit/{safari_ver} (KHTML, like Gecko) Version/{random.randint(14, 17)}.0 Safari/{safari_ver}"
    elif 浏览器 == "edge":
        ua = f"Mozilla/5.0 ({sys_block}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{chrome_ver}"
    elif 浏览器 == "opera":
        ua = f"Mozilla/5.0 ({sys_block}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 OPR/{chrome_ver}"
    else:
        ua = f"Mozilla/5.0 ({sys_block}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"

    return ua