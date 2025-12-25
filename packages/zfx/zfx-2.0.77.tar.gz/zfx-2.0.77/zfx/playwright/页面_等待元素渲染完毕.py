def 页面_等待元素渲染完毕(页面, 选择器: str, 状态: str = "visible", 超时毫秒: int = 30000):
    """
    功能：
        等待指定元素达到目标状态（默认：可见），用于解决页面尚未渲染完成就取元素导致的异常。
        常用于：首次加载列表容器、弹层出现/消失、加载指示器的显示/隐藏等。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 选择器：字符串，CSS 选择器。如 ".SearchProductGrid-module__container___jew-i"、"#login"、"div.card > a"。
        - 状态：字符串，等待的目标状态。
            可选：
                "attached" → 元素出现在 DOM（不要求可见）
                "visible"  → 元素出现在 DOM 且可见（默认）
                "hidden"   → 元素在 DOM 中但不可见，或不存在
                "detached" → 元素从 DOM 移除
        - 超时毫秒：整数，最大等待时间（默认 30000 毫秒 = 30s）。

    返回值：
        - True  ：等待成功（元素已达到目标状态）
        - False ：等待失败（超时或异常），并打印错误信息

    注意：
        1) 若页面为异步渲染，建议先等待容器 "visible"，再做后续查询。
        2) 等待元素消失可用 state="hidden" 或 "detached"（根据你的语义选择）。
        3) 若你的目标元素属于 iframe/Shadow DOM，需要先切到对应上下文再等待。

    使用示例：
        # 等待商品容器渲染完成（可见）
        页面_等待元素渲染完毕(页面, ".SearchProductGrid-module__container___jew-i", 状态="visible", 超时毫秒=20000)

        # 等待加载动画消失
        页面_等待元素渲染完毕(页面, ".loading-spinner", 状态="hidden")

        # 等待弹窗从 DOM 移除
        页面_等待元素渲染完毕(页面, "#dialog-root", 状态="detached")
    """
    try:
        页面.wait_for_selector(选择器, state=状态, timeout=超时毫秒)
        return True
    except Exception as e:
        print(f"等待元素渲染失败：selector={选择器}, state={状态}, timeout={超时毫秒}，错误：{e}")
        return False