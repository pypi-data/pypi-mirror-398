def 页面_获取元素子项数量(页面, 容器选择器: str, 子项选择器: str):
    """
    功能：
        获取某个容器下子项元素的数量。
        常用于统计当前页面上有多少个产品/卡片/列表项。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 容器选择器：字符串，父容器的 CSS 选择器。
            例如 ".SearchProductGrid-module__container___jew-i"
        - 子项选择器：字符串，子元素的 CSS 选择器。
            例如 "li"、".card"、"div.product-item"

    返回值：
        - 成功：返回整数，表示子项数量。
        - 失败：返回 False，并打印错误信息。

    注意：
        1) 本函数为即时统计，不会等待渲染。
           若页面异步加载，请先调用 页面_等待元素渲染完毕 或 页面_等待元素子项数量。
        2) 返回的数量可能为 0，需结合业务逻辑判断是否正常。

    使用示例：
        # 统计当前产品数量
        数量 = 页面_获取元素子项数量(页面,
                           容器选择器=".SearchProductGrid-module__container___jew-i",
                           子项选择器="li")
        print("当前产品数量：", 数量)

        if 数量 >= 100:
            print("任务完成！")
    """
    try:
        选择器 = f"{容器选择器} {子项选择器}".strip()
        元素列表 = 页面.query_selector_all(选择器)
        return len(元素列表)
    except Exception as e:
        print(f"获取子项数量失败：容器={容器选择器}, 子项={子项选择器}, 错误：{e}")
        return False
