def 页面_访问网页(页面, 地址, 等待秒数: int = 0):
    """
    使用指定的页面对象访问目标网址。

    参数：
        - 页面：Playwright 的页面对象（由 初始化_普通模式 返回的字典中 "页面" 字段）。
        - 地址：字符串，要访问的网址。例如 "https://example.com"。
        - 等待秒数：可选。访问后是否等待指定秒数，默认 0 表示不等待。
            - 传入 >0 的值，则在加载完成后额外 sleep 指定秒数。

    返回值：
        - 成功时返回 True。
        - 如果失败，返回 False，并打印异常信息。

    使用示例：
        结果 = 初始化_普通模式()
        if 结果:
            页面 = 结果["页面"]
            页面_访问网页(页面, "https://example.com", 等待秒数=3)
            print("标题：", 页面.title())

            # 关闭
            结果["上下文"].close()
            结果["浏览器"].close()
            结果["引擎"].stop()
    """
    try:
        页面.goto(地址)
        if 等待秒数 > 0:
            import time
            time.sleep(等待秒数)
        return True
    except Exception as e:
        print("访问网页失败：", e)
        return False