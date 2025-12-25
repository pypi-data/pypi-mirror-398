def 页面_删除元素子项(页面, 容器选择器: str, 子项选择器: str):
    """
    功能：
        删除指定容器下的所有子项元素。
        常用于清空列表、移除广告卡片、或在测试中重置页面状态。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 容器选择器：字符串，父容器 CSS 选择器。
            例如 ".container"、"#main"
        - 子项选择器：字符串，子元素 CSS 选择器。
            例如 "li"、".card"、"div.product"

    返回值：
        - True  ：删除成功
        - False ：失败，并打印错误信息

    注意：
        1) 选择器会拼接为 f"{容器选择器} {子项选择器}"，请确保层级关系正确。
        2) 若只想删除某一类元素（而非全部），可在 子项选择器 中加入更精确的条件。
        3) 删除操作不可恢复，执行后 DOM 节点会被移除。

    使用示例：
        # 删除容器下的所有 li
        页面_删除元素子项(页面, ".SearchProductGrid-module__container___jew-i", "li")

        # 删除容器下的所有 class="ad" 的卡片
        页面_删除元素子项(页面, ".main-list", ".ad")
    """
    try:
        选择器 = f"{容器选择器} {子项选择器}".strip()
        页面.evaluate(f"""
            (sel) => {{
                const els = document.querySelectorAll(sel);
                els.forEach(el => el.remove());
            }}
        """, 选择器)
        return True
    except Exception as e:
        print(f"删除子项元素失败：容器={容器选择器}, 子项={子项选择器}, 错误：{e}")
        return False