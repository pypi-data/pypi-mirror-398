from playwright.sync_api import sync_playwright


def 初始化_普通模式(浏览器路径=None, 启动参数=None):
    """
    初始化 Playwright 浏览器，并返回中文对象“四件套”。

    功能说明:
        封装浏览器启动流程，统一返回:
            - "引擎": Playwright 引擎对象（进程入口，最终需 stop()）
            - "浏览器": 浏览器对象（相当于浏览器进程实例）
            - "上下文": 浏览器上下文（独立的用户态，可视为“无痕/配置隔离空间”）
            - "页面": 页面对象（单标签页，大部分页面操作在此完成）

        设计目标:
            - 降低上手门槛：调用方无需关心底层启动细节；
            - 统一资源回收：有明确的关闭顺序，减少“忘记 stop/close”的风险；
            - 兼容常见启动场景：支持无头模式、沙盒问题、窗口最大化等参数透传。

    前置条件:
        1) 已安装 Playwright 的 Python 依赖与浏览器内核:
            - pip install playwright
            - playwright install     # 或 playwright install chromium
        2) 若需指定系统 Chrome/Edge 可执行文件，提供“浏览器路径”绝对路径。

    Args:
        浏览器路径 (str | None):
            浏览器可执行文件路径。
            - 为空: 使用 Playwright 内置的 Chromium。
            - 传入路径: 使用该可执行文件（例如
              "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"）。
        启动参数 (list[str] | None):
            浏览器原生启动参数列表（透传）。常见示例:
              - "--headless"        → 无界面模式（服务器更常用）
              - "--disable-gpu"     → 禁用 GPU 加速
              - "--no-sandbox"      → 规避某些 Linux 权限问题
              - "--start-maximized" → 启动最大化窗口
            说明: 本函数内部以是否包含 "--headless" 判断是否启用无头模式。

    Returns:
        dict | bool:
            - 成功: 返回包含 "引擎"、"浏览器"、"上下文"、"页面" 的字典。
            - 失败: 返回 False，并打印错误信息（调用方无需再 try/except）。

    使用示例(推荐配合 zfx 封装的页面操作函数):
        结果 = 初始化_普通模式(启动参数=["--headless"])
        if 结果:
            页 = 结果["页面"]
            # 使用 zfx.playwright 的二次封装而非原生 API，语义更统一:
            # 页面_访问网页(页, "https://example.com", 等待秒数=2)
            # 文本 = 页面_获取元素文本(页, "h1")
            # ...
            # 关闭顺序（建议封装在 finally 中）:
            结果["上下文"].close()
            结果["浏览器"].close()
            结果["引擎"].stop()

    关闭顺序:
        页面 → 上下文 → 浏览器 → 引擎
        说明: 关闭“上下文”会隐式释放其下所有“页面”，但保持显式顺序可读性更佳。

    常见问题:
        - 启动报错 Executable doesn't exist:
            仅安装了 pip 依赖，未执行 `playwright install` 下载浏览器内核。
        - Linux 上权限/依赖报错:
            尝试: `playwright install chromium --with-deps` 安装系统依赖。
        - 下载过慢:
            为 pip 配置国内镜像；或为 `playwright install` 配置 HTTP(S) 代理。
        - 无头与有头切换:
            由 `启动参数` 中是否包含 "--headless" 决定。

    注意:
        - 内部说明尽量避免出现 Playwright 原生 API 代码片段，以免误导二次封装用户。
        - 如需更强的可定制性（代理、默认超时、持久化上下文等），可在后续扩展版
          `初始化_*` 函数中提供专用参数（保持该函数简单稳定）。

    免责声明:
        本函数与说明仅用于学习与研究，使用请遵循目标网站与相关法律法规。
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

        return {
            "引擎": 引擎,
            "浏览器": 浏览器,
            "上下文": 上下文,
            "页面": 页面
        }
    except Exception as e:
        print("浏览器初始化失败：", e)
        return False
