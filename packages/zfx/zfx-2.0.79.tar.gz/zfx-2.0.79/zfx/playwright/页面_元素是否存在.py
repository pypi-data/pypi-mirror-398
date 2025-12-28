def 页面_元素是否存在(页面, 选择器: str, 等待毫秒: int = 0):
    """
    功能：
        判断页面中是否存在指定元素。
        可用于按钮、输入框、弹窗等元素是否出现的判断。

    参数：
        - 页面：Playwright 页面对象（sync）。
        - 选择器：字符串，CSS 选择器。例如 "#login"、".btn-submit"。
        - 等待毫秒：整数，可选。
            - 默认 0 → 立即判断是否存在。
            - >0    → 最多等待指定毫秒，看元素是否出现。

    返回值：
        - True  ：元素存在
        - False ：元素不存在或异常

    使用示例：
        if 页面_元素是否存在(页面, "button#login"):
            print("登录按钮存在")

        if 页面_元素是否存在(页面, ".popup-dialog", 等待毫秒=5000):
            print("5 秒内弹窗出现")
    """
    try:
        if 等待毫秒 > 0:
            页面.wait_for_selector(选择器, timeout=等待毫秒)
            return True
        else:
            return 页面.query_selector(选择器) is not None
    except Exception:
        return False
