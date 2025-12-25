def 屏蔽_网页资源_自定义(驱动器对象, 屏蔽列表):
    """
    使用 Chrome DevTools 协议（CDP）屏蔽网页中指定的资源类型。

    适用于自动化浏览器环境，用户可自定义需要屏蔽的资源 URL 模式，
    提高页面加载速度，节省网络资源。（建议在浏览器初始化后立即调用）

    参数：
        - 驱动器对象：Selenium Chrome 浏览器驱动对象（webdriver.Chrome 实例）
        - 屏蔽列表（list）：包含 URL 通配符的字符串列表，表示要屏蔽的资源。例如：
            [
                "*.css",                           # 样式表文件
                "*.svg",                           # 矢量图标（LOGO、图标按钮）
                "*.png", "*.jpg", "*.jpeg", "*.gif",  # 图片资源
                "*.woff", "*.woff2", "*.ttf", "*.otf", # 字体资源
                "*.mp4", "*.mp3", "*.webm"          # 视频 / 音频资源
            ]

    注意事项：
        1. 需使用 Chrome 浏览器，并通过 Selenium 驱动启动。
        2. 每次调用会覆盖当前的屏蔽设置，请传入完整的资源屏蔽列表。
        3. URL 模式支持通配符 *，匹配任意字符，可用于屏蔽资源路径、文件名或域名片段。
        4. CDP 屏蔽仅在当前会话生效，浏览器关闭后失效。

    返回值：
        - 无返回值。屏蔽配置将在当前页面加载流程中立即生效。
    """
    try:
        驱动器对象.execute_cdp_cmd("Network.enable", {})
        驱动器对象.execute_cdp_cmd("Network.setBlockedURLs", {
            "urls": 屏蔽列表
        })
    except Exception:
        pass