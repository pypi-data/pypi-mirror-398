import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def 等待元素可点击_快速(驱动器对象, 定位方法, 定位值, 超时时间=30):
    """
    等待元素可点击。相较于普通的：等待元素可点击 命令返回速度更快，普通的偏向于稳定性，会在元素加载完毕后等待一秒返回，这个快速模式则会直接返回！

    参数：
        - 驱动器对象: 浏览器驱动对象。
        - 定位方法: 用于定位元素的方式（不需要输入 By.），例如:
            - "ID": 通过元素的 ID 属性定位。
            - "XPATH": 通过元素的 XPATH 路径定位。
            - "NAME": 通过元素的 NAME 属性定位。
            - "CSS_SELECTOR": 通过 CSS 选择器定位。
            - "CLASS_NAME": 通过元素的 CLASS 属性定位。
        - 定位值: 元素的具体定位值，例如元素的 ID、XPATH 等。
        - 超时时间: 最大等待时间，默认 30 秒。

    返回值：
        - 成功返回可点击的元素对象。
        - 超时或失败返回 None。
    """
    try:
        # 使用 getattr 动态获取 By 类中的常量
        定位方法常量 = getattr(By, 定位方法.upper())

        # 使用 WebDriverWait 等待元素可点击
        元素对象 = WebDriverWait(驱动器对象, 超时时间).until(EC.element_to_be_clickable((定位方法常量, 定位值)))

        return 元素对象  # 返回元素对象
    except Exception:
        return None  # 超时或发生异常时返回 None