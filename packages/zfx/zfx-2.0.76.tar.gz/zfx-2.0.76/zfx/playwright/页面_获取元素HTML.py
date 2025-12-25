def 页面_获取元素HTML(页面, 选择器: str, 等待可见: bool = True, 超时毫秒: int = 30000):
    """
    功能：
        获取指定元素的 innerHTML（元素内部的原始 HTML 字符串）。
        默认先等待该元素可见，再调用 Playwright 的 page.inner_html() 获取内容。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 选择器：字符串，CSS 选择器。例如：
                 "#main"、".card .title"、"div.list > ul > li:nth-child(1)"。
        - 等待可见：布尔，是否在获取前等待元素可见（state="visible"），默认 True。
        - 超时毫秒：整数，等待的最大时长（仅在 等待可见=True 时生效），默认 30000 毫秒。

    返回值：
        - 成功：返回 innerHTML 的字符串内容。
        - 失败：返回 False，并打印错误信息。

    注意：
        1) 若选择器匹配多个元素，本函数返回“第一个匹配元素”的 innerHTML。
        2) 若页面是异步渲染，建议保持 等待可见=True（默认），更稳。
        3) 若目标元素在 iframe 或 Shadow DOM 中，需要先切换到对应上下文后再调用。
        4) 如需 outerHTML / 纯文本，可另写：
           - 页面.eval_on_selector(选择器, "el => el.outerHTML")
           - 页面.inner_text(选择器)

    使用示例：
        # 访问页面
        # 结果 = 初始化_普通模式()
        # 页面 = 结果["页面"]
        # 页面_访问网页(页面, "https://www.xbox.com/en-US/games/browse")

        容器 = ".SearchProductGrid-module__container___jew-i"
        html = 页面_获取元素HTML(页面, 容器)
        if html is not False:
            print("容器 innerHTML 长度：", len(html))
        else:
            print("获取失败")
    """
    try:
        if 等待可见:
            页面.wait_for_selector(选择器, state="visible", timeout=超时毫秒)
        return 页面.inner_html(选择器)
    except Exception as e:
        print(f"获取元素HTML失败：selector={选择器}，错误：{e}")
        return False
