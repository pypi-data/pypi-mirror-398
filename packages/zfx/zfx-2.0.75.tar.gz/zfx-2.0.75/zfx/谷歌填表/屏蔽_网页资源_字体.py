def 屏蔽_网页资源_字体(驱动器对象):
    """
    屏蔽网页中的字体资源，适用于优化加载速度、减少网页美化资源占用。

    参数：
        - 驱动器对象：Selenium Chrome 浏览器驱动对象（webdriver.Chrome 实例）

    功能说明：
        本函数通过 Chrome DevTools 协议（CDP）屏蔽网页中使用的外部字体资源，
        通常用于在自动化环境中避免字体下载所带来的延迟，尤其在表单填报、爬取数据等纯文本任务中效果显著。

        屏蔽的字体资源类型包括：
            - *.woff：Web Open Font Format
            - *.woff2：压缩版的 WOFF
            - *.ttf：TrueType 字体
            - *.otf：OpenType 字体

    返回值：
        - 无返回值。CDP 命令成功执行后立即生效于当前页面加载行为。

    注意事项：
        1. 需使用 Chrome 浏览器并通过 Selenium 启动。
        2. 每次调用将替换当前屏蔽列表，如需组合多个资源请合并后传入或使用组合函数。
        3. 屏蔽字体资源不会影响页面文本内容，但会导致使用默认字体渲染。

    使用示例：
        from zfx.谷歌填表 import 屏蔽_网页资源_字体

        驱动器对象 = 初始化_普通模式(浏览器路径, 驱动器路径)
        屏蔽_网页资源_字体(驱动器对象)
    """
    try:
        驱动器对象.execute_cdp_cmd("Network.enable", {})
        驱动器对象.execute_cdp_cmd("Network.setBlockedURLs", {
            "urls": ["*.woff", "*.woff2", "*.ttf", "*.otf"]
        })
    except Exception:
        pass