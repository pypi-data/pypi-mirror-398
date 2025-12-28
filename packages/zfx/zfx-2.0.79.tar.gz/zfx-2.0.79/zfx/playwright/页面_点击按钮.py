def 页面_点击按钮(页面, 名称: str):
    """
    点击指定名称的按钮。

    参数：
        - 页面：Playwright 的页面对象（由 初始化_普通模式 返回的字典中 "页面" 字段）。
        - 名称：字符串，按钮的可访问名称（渲染后用户实际看到/读到的文字，或 aria-label 的值）。

    定位规则：
        - Playwright 使用 get_by_role("button", name=名称) 定位元素。
        - name 来源包括：
            1. 按钮内的可见文字，例如 <button>提交</button> → 名称="提交"
            2. aria-label 属性，例如 <button aria-label="提交"></button> → 名称="提交"
            3. aria-labelledby 指定的文本
        - 所以 "名称" 并不是 class 或 id，而是用户在页面上看到的文字。

    返回值：
        - True：点击成功
        - False：失败，并打印异常信息

    使用示例：
        结果 = 初始化_普通模式()
        if 结果:
            页面 = 结果["页面"]
            页面_访问网页(页面, "https://example.com", 等待秒数=2)

            页面_点击按钮(页面, "Load more")  # 点击名称为“Load more”的按钮

            # 关闭
            结果["上下文"].close()
            结果["浏览器"].close()
            结果["引擎"].stop()
    """
    try:
        页面.get_by_role("button", name=名称).click()
        return True
    except Exception as e:
        print("点击按钮失败：", e)
        return False
