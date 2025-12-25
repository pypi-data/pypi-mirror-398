def 页面_获取元素列表(页面, 容器选择器: str, 标签: str = None):
    """
    功能：
        获取指定容器下的多个元素对象，并以列表形式返回。
        可用于批量处理，如遍历商品卡片、列表项等。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 容器选择器：字符串，CSS 选择器，用于定位父容器。
            例如 ".list-container"、"#main"。
        - 标签：字符串，可选。若传入则查找容器下的指定标签，
            常见示例：
                "li"    → 列表项
                "div"   → 普通块级元素
                "span"  → 行内容器（常用于文字片段）
                "a"     → 超链接
                "img"   → 图片
                "input" → 输入框
                "button"→ 按钮
                "p"     → 段落
                "h1"~"h6" → 标题标签
            若不传，仅返回容器自身。

    返回值：
        - 成功：返回元素对象列表（可能为空列表）。
        - 失败：返回 False，并打印错误信息。

    注意：
        1) 若需获取元素文本内容，可配合 页面_获取元素文本()。
        2) 返回的为元素对象列表，可继续 query_selector / inner_text 等操作。
        3) 若目标元素在 iframe/Shadow DOM 内，请先切换上下文。

    使用示例：
        # 获取容器下的所有 li 项
        列表 = 页面_获取元素列表(页面, ".SearchProductGrid-module__container___jew-i", "li")
        print("找到数量：", len(列表))

        # 获取容器下的所有 a 链接
        链接们 = 页面_获取元素列表(页面, ".nav-bar", "a")
        for 链接 in 链接们:
            print("链接文本：", 链接.inner_text())

        # 获取容器自身
        容器 = 页面_获取元素列表(页面, ".SearchProductGrid-module__container___jew-i")
        print("容器数量：", len(容器))
    """
    try:
        if 标签:
            选择器 = f"{容器选择器} {标签}"
        else:
            选择器 = 容器选择器
        元素列表 = 页面.query_selector_all(选择器)
        return 元素列表 if 元素列表 else []
    except Exception as e:
        print(f"获取元素列表失败：容器={容器选择器}, 标签={标签}, 错误：{e}")
        return False
