from playwright.sync_api import sync_playwright


def 初始化_禁用图片(浏览器路径=None, 启动参数=None):
    """
    初始化 Playwright 浏览器（禁用图片加载），并返回中文对象。

    参数：
        - 浏览器路径：可选。浏览器可执行文件路径，例如：
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
          如果不指定，Playwright 会使用默认安装的 Chromium 内核。

        - 启动参数：可选。启动浏览器时的自定义参数（列表形式），例如：
            ["--headless", "--disable-gpu", "--no-sandbox"]

    返回值：
        - 成功时返回一个包含四个对象的字典：
            {
                "引擎":   Playwright 引擎对象（最后需要 stop() 停止）
                "浏览器": 浏览器对象（相当于整个浏览器进程）
                "上下文": 浏览器上下文（独立的用户环境，可以有多个）
                "页面":   页面对象（单个标签页，主要操作都在这里，已禁用图片）
            }
        - 如果失败，返回 False 并打印错误信息。

    使用示例：
        结果 = 初始化_禁用图片(启动参数=["--headless"])
        if 结果:
            页面 = 结果["页面"]
            页面.goto("https://example.com")
            print("标题：", 页面.title())

            # 关闭顺序
            结果["上下文"].close()
            结果["浏览器"].close()
            结果["引擎"].stop()
    """
    try:
        引擎 = sync_playwright().start()

        参数列表 = 启动参数 if 启动参数 else []

        浏览器 = 引擎.chromium.launch(
            headless="--headless" in 参数列表,
            args=参数列表,
            executable_path=浏览器路径 if 浏览器路径 else None
        )

        上下文 = 浏览器.new_context()
        页面 = 上下文.new_page()

        # 屏蔽图片请求
        def 拦截(route, request):
            if request.resource_type == "image":
                route.abort()
            else:
                route.continue_()

        页面.route("**/*", 拦截)

        return {
            "引擎": 引擎,
            "浏览器": 浏览器,
            "上下文": 上下文,
            "页面": 页面
        }
    except Exception as e:
        print("浏览器初始化失败：", e)
        return False