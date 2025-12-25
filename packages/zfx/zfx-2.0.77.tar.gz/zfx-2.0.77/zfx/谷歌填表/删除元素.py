from selenium.webdriver.common.by import By


def 删除元素(驱动器对象, 定位方法, 定位值):
    """
    删除页面上的指定元素。

    参数：
        - 驱动器对象: 浏览器驱动对象。
        - 定位方法: 用于定位元素的方式（不需要输入 By.），例如:
            - "ID": 通过元素的 ID 属性定位。
            - "XPATH": 通过元素的 XPATH 路径定位。
            - "NAME": 通过元素的 NAME 属性定位。
            - "CSS_SELECTOR": 通过 CSS 选择器定位。
            - "CLASS_NAME": 通过元素的 CLASS 属性定位。
        - 定位值: 元素的具体定位值，例如元素的 ID、XPATH 等。

    返回值：
        - 成功返回 True，表示元素已被删除。
        - 如果发生异常或定位失败，返回 False。
    """
    try:
        # 使用 getattr 动态获取 By 类中的常量
        定位方法常量 = getattr(By, 定位方法.upper())

        # 定位目标元素
        元素对象 = 驱动器对象.find_element(定位方法常量, 定位值)

        # 使用 JavaScript 删除目标元素
        驱动器对象.execute_script("arguments[0].remove();", 元素对象)

        return True  # 删除成功返回 True
    except Exception:
        return False  # 删除失败返回 False
