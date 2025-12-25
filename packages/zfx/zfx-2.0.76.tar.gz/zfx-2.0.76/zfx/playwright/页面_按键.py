def 页面_按键(页面, 键值: str, 选择器: str = None):
    """
    在页面或指定元素上模拟按键操作。

    参数：
        - 页面：Playwright 的页面对象。
        - 键值：字符串，按键名称或键代码。
            常见示例：
                "Enter"       → 回车
                "Tab"         → Tab 键
                "Escape"      → Esc 键
                "ArrowUp"     → 方向上
                "ArrowDown"   → 方向下
                "F5"          → 刷新
                "Control+A"   → Ctrl+A
                "KeyA"        → A 键
                "Digit1"      → 数字 1 键
        - 选择器：可选。传入时表示对某个元素触发按键。
                 不传时表示对当前焦点（页面.keyboard）触发。

    返回值：
        - True：成功
        - False：失败，并打印异常信息

    使用示例：
        页面_按键(页面, "Enter")                   # 在当前焦点按回车
        页面_按键(页面, "Enter", "input[name='q']") # 在搜索框按回车
        页面_按键(页面, "Control+A")                # Ctrl+A 全选
    """
    try:
        if 选择器:
            页面.press(选择器, 键值)
        else:
            页面.keyboard.press(键值)
        return True
    except Exception as e:
        print("按键操作失败：", e)
        return False