def 页面_取网页源码(页面, 保存到文件: str = None):
    """
    获取当前页面的完整 HTML 源码。

    参数：
        - 页面：Playwright 的页面对象（由 初始化_普通模式 返回的字典中 "页面" 字段）。
        - 保存到文件：可选。传入路径时会把源码写入到该文件（UTF-8 编码）。

    返回值：
        - 成功时返回 HTML 源码字符串。
        - 如果失败，返回 False，并打印异常信息。

    使用示例：
        结果 = 初始化_普通模式()
        if 结果:
            页面 = 结果["页面"]
            页面_访问网页(页面, "https://example.com", 等待秒数=2)

            html = 页面_取网页源码(页面, 保存到文件="example.html")
            print("源码长度：", len(html))

            # 关闭
            结果["上下文"].close()
            结果["浏览器"].close()
            结果["引擎"].stop()
    """
    try:
        html = 页面.content()
        if 保存到文件:
            with open(保存到文件, "w", encoding="utf-8") as f:
                f.write(html)
        return html
    except Exception as e:
        print("获取网页源码失败：", e)
        return False