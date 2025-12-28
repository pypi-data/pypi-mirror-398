from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # 导入Service


def 初始化_禁用图片(浏览器路径, 驱动器路径, 启动参数=None):
    """
    初始化谷歌浏览器，禁用图片加载，适用于提升无关图片资源的加载速度。

    参数：
        - 浏览器路径: Chrome 浏览器的可执行文件路径。例如 "/usr/bin/google-chrome" 或 "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"。
        - 驱动器路径: ChromeDriver 驱动器的路径。例如 "/usr/bin/chromedriver" 或 "C:\\chromedriver\\chromedriver.exe"。
        - 启动参数: 可选参数，启动浏览器时的自定义参数，列表形式，例如 ["--headless", "--incognito", "--disable-gpu"]。
            - 常见启动参数示例：
            - "--headless"：以无界面模式启动浏览器，适用于服务器环境。
            - "--disable-gpu"：禁用 GPU 硬件加速，通常与无头模式一起使用。
            - "--incognito"：启动浏览器的隐私模式（无痕浏览）。
            - "--no-sandbox"：禁用沙盒，通常用于避免权限问题（需要谨慎使用）。

    返回值：
        - 成功时返回浏览器驱动器对象，可用于与页面进行交互。
        - 初始化失败时返回 False。

    注意事项：
        1. 禁用图片加载有助于提升页面加载速度，适合不需要查看图片内容的场景，例如网页抓取和自动化测试。
        2. 确保 Chrome 和 ChromeDriver 版本匹配，以避免浏览器无法启动的问题。

    使用示例：
        - 浏览器路径 = "/path/to/chrome"
        - 驱动器路径 = "/path/to/chromedriver"
        - 启动参数 = ["--headless", "--disable-gpu"]

        驱动器对象 = zfx.谷歌填表.初始化_禁用图片(浏览器路径, 驱动器路径, 启动参数)

        if 驱动器对象:
            print("浏览器启动成功")
            驱动器对象.get("https://example.com")  # 打开网址
        else:
            print("浏览器启动失败")
    """
    try:
        chrome选项 = Options()

        # 设置浏览器的可执行文件路径
        chrome选项.binary_location = 浏览器路径

        # 禁用图片加载，提升网页加载速度
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome选项.add_experimental_option("prefs", prefs)

        # 添加自定义的启动参数
        if 启动参数:
            for 参数 in 启动参数:
                chrome选项.add_argument(参数)

        # 使用Service对象来设置驱动器路径
        服务 = Service(驱动器路径)

        # 启动浏览器
        驱动器对象 = webdriver.Chrome(service=服务, options=chrome选项)

        return 驱动器对象  # 成功返回浏览器对象
    except Exception:
        return False  # 失败返回 False