def 页面_点击元素(页面, 选择器: str, 等待可见: bool = True, 超时毫秒: int = 30000):
    """
    功能：
        点击指定选择器对应的元素。
        用于 class、id、属性选择器等方式定位按钮/链接/任意可点击元素。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 选择器：字符串，CSS 选择器。例如：
            "#submit"、".btn-login"、"button[type='submit']"
        - 等待可见：布尔，是否在点击前等待元素可见，默认 True。
        - 超时毫秒：整数，等待的最大时长（仅在 等待可见=True 时生效），默认 30000 毫秒。

    返回值：
        - True：点击成功
        - False：失败，并打印异常信息

    使用示例：
        # 点击 id="submit" 的按钮
        页面_点击元素(页面, "#submit")

        # 点击 class="btn-login" 的按钮
        页面_点击元素(页面, ".btn-login")

        # 点击带有自定义属性的按钮
        页面_点击元素(页面, "button[data-testid='login']")
    """
    try:
        if 等待可见:
            页面.wait_for_selector(选择器, state="visible", timeout=超时毫秒)
        页面.click(选择器)
        return True
    except Exception as e:
        print(f"点击元素失败：selector={选择器}, 错误：{e}")
        return False
