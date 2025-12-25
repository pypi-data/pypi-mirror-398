def 页面_获取元素文本(页面, 选择器: str, 等待可见: bool = True, 超时毫秒: int = 30000,
               去除首尾空白: bool = True, 折叠空白: bool = True):
    """
    功能：
        获取指定元素的可见文本（Playwright 的 page.inner_text()）。
        默认在获取前等待元素“可见”，并对文本做基础清洗（去首尾空白、折叠连续空白）。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 选择器：字符串，CSS 选择器。如 "#main"、".card .title"、"ul > li:nth-child(1)"。
        - 等待可见：布尔，在获取前是否等待元素可见（state="visible"），默认 True。
        - 超时毫秒：整数，等待最大时长（仅在 等待可见=True 时生效），默认 30000 毫秒。
        - 去除首尾空白：布尔，是否对结果执行 str.strip()，默认 True。
        - 折叠空白：布尔，是否把连续空白压缩成单个空格（含换行/制表），默认 True。

    返回值：
        - 成功：返回处理后的文本字符串。
        - 失败：返回 False，并打印错误信息。

    注意：
        1) 若选择器匹配多个元素，本函数返回“第一个匹配元素”的文本。
        2) inner_text() 只返回“可见文本”，隐藏元素内容不会被包含；
           若需拿到 textContent，可使用：
             页面.eval_on_selector(选择器, "el => el.textContent")
        3) 若元素在 iframe/Shadow DOM 内，请先切换到对应上下文。

    使用示例：
        # 获取容器标题文本
        文本 = 页面_获取元素文本(页面, ".SearchProductGrid-module__container___jew-i .ProductCard-module__title___nHGIp")
        if 文本 is not False:
            print("标题：", 文本)

        # 仅出现即可（不要求可见），就把 等待可见=False
        文本2 = 页面_获取元素文本(页面, "#hidden-info", 等待可见=False)
    """
    import re
    try:
        if 等待可见:
            页面.wait_for_selector(选择器, state="visible", timeout=超时毫秒)
        文本 = 页面.inner_text(选择器)
        if 去除首尾空白 and isinstance(文本, str):
            文本 = 文本.strip()
        if 折叠空白 and isinstance(文本, str):
            文本 = re.sub(r"\s+", " ", 文本)
        return 文本
    except Exception as e:
        print(f"获取元素文本失败：selector={选择器}，错误：{e}")
        return False