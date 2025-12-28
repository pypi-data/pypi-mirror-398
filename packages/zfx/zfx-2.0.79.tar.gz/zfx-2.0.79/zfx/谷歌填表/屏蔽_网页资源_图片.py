def 屏蔽_网页资源_图片(驱动器对象):
    """
    屏蔽网页中的图片资源，适用于自动化脚本中提升加载速度、减少资源占用。

    参数：
        - 驱动器对象：Selenium Chrome 浏览器驱动对象（webdriver.Chrome 实例）

    功能说明：
        本函数通过 Chrome DevTools 协议（CDP）屏蔽网页中的图片资源，
        避免加载图片造成页面延迟或带宽占用。适合用于表单填报、数据提取等对图像无关的场景。

        屏蔽的图片资源类型包括：
            - *.jpg：常见网页图片格式
            - *.jpeg：JPG 的另一种扩展格式
            - *.png：透明图、界面图常用格式
            - *.gif：动图格式

    返回值：
        - 无返回值。CDP 命令成功执行后立即生效于当前页面加载行为。

    注意事项：
        1. 该功能依赖于 Chrome 浏览器的 DevTools 协议（CDP），仅适用于通过 Selenium 启动的 Chrome。
        2. 每次调用会替换之前的屏蔽规则，若需要组合屏蔽，请使用 zfx 中的其他组合函数或手动传参。
        3. 本函数不影响页面结构，仅影响资源下载，屏蔽后页面上可能出现图片加载失败的图标或占位。

    使用示例：
        from zfx.谷歌填表 import 屏蔽_网页资源_图片

        驱动器对象 = 初始化_普通模式(浏览器路径, 驱动器路径)
        屏蔽_网页资源_图片(驱动器对象)
    """
    try:
        驱动器对象.execute_cdp_cmd("Network.enable", {})
        驱动器对象.execute_cdp_cmd("Network.setBlockedURLs", {
            "urls": ["*.jpg", "*.jpeg", "*.png", "*.gif"]
        })
    except Exception:
        pass