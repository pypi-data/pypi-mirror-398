def 页面_删除元素(页面, 选择器: str):
    """
    删除页面中符合选择器的所有元素。

    参数：
        - 页面：Playwright 的页面对象（由 初始化_普通模式 返回的字典中 "页面" 字段）。
        - 选择器：字符串，CSS 选择器，用于定位要删除的元素。
            常见示例：
                "#id值"                   → 按 id 删除
                ".class值"                → 按 class 删除
                "div.banner"              → 删除所有 class="banner" 的 div
                "#广告横幅, .popup"        → 同时删除多个选择器

    返回值：
        - True：删除成功
        - False：失败，并打印异常信息

    使用示例：
        结果 = 初始化_普通模式()
        if 结果:
            页面 = 结果["页面"]
            页面_访问网页(页面, "https://example.com", 等待秒数=2)

            页面_删除元素(页面, "#广告横幅")    # 删除 id="广告横幅" 的元素
            页面_删除元素(页面, ".popup")       # 删除所有 class="popup" 的弹窗

            # 关闭
            结果["上下文"].close()
            结果["浏览器"].close()
            结果["引擎"].stop()
    """
    try:
        页面.evaluate(f"""
            (sel) => {{
                const els = document.querySelectorAll(sel);
                els.forEach(el => el.remove());
            }}
        """, 选择器)
        return True
    except Exception as e:
        print("删除元素失败：", e)
        return False
