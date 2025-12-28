def 页面_输入文本(页面, 选择器: str, 文本: str, 延迟: int = 0):
    """
    在指定的输入框中输入文本。

    参数：
        - 页面：Playwright 的页面对象（由 初始化_普通模式 返回的字典中 "页面" 字段）。
        - 选择器：字符串，用于定位输入框的 CSS 选择器。
            常见写法示例：
                "#id值"                  → 按 id 定位
                ".class值"               → 按 class 定位
                "input[name='q']"        → 按 name 属性定位
                "form.login input[type='text']" → 组合选择器
        - 文本：要输入的字符串。
        - 延迟：可选。逐字输入时每个字符的间隔（毫秒）。
            - 默认 0 → 直接填充（推荐，快且稳定）。
            - >0    → 模拟人工逐字输入（更真实）。

    返回值：
        - 成功时返回 True。
        - 如果失败，返回 False，并打印异常信息。

    使用示例：
        页面_输入文本(页面, "input[name='wd']", "Playwright Python")
        页面_输入文本(页面, "#username", "fengxiang", 延迟=100)
    """
    try:
        if 延迟 > 0:
            页面.type(选择器, 文本, delay=延迟)
        else:
            页面.fill(选择器, 文本)
        return True
    except Exception as e:
        print("输入文本失败：", e)
        return False
