def 屏蔽_网页资源_图标(驱动器对象):
    """
    屏蔽网页中的 SVG 矢量图标资源，适用于精简页面视觉加载内容。

    参数：
        - 驱动器对象：Selenium Chrome 浏览器驱动对象（webdriver.Chrome 实例）

    功能说明：
        本函数通过 Chrome DevTools 协议（CDP）屏蔽网页中常见的图标格式，尤其是 SVG 矢量图，
        用于减少页面视觉元素占用资源，适合执行自动化任务时简化界面渲染，提升执行效率。

        屏蔽的图标资源类型包括：
            - *.svg：常见图标、按钮、LOGO 使用的矢量格式

    返回值：
        - 无返回值。CDP 命令成功执行后立即生效于当前页面加载行为。

    注意事项：
        1. 本功能需配合 Chrome 浏览器和 Selenium 驱动器使用。
        2. 每次调用会替换原有的屏蔽列表，如需联合屏蔽多个类型，请使用组合函数或手动合并屏蔽项。
        3. 屏蔽图标不会影响功能性，仅影响图像展示，页面可能出现图标占位。

    使用示例：
        from zfx.谷歌填表 import 屏蔽_网页资源_图标

        驱动器对象 = 初始化_普通模式(浏览器路径, 驱动器路径)
        屏蔽_网页资源_图标(驱动器对象)
    """
    try:
        驱动器对象.execute_cdp_cmd("Network.enable", {})
        驱动器对象.execute_cdp_cmd("Network.setBlockedURLs", {
            "urls": ["*.svg"]
        })
    except Exception:
        pass