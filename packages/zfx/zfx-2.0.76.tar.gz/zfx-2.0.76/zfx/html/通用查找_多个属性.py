from bs4 import BeautifulSoup


def 通用查找_多个属性(html文本, 标签名, 属性字典):
    """
    从给定的HTML文本中，根据标签名和多个属性查找元素，并返回包含这些元素的列表。

    参数:
        html文本 (str): HTML 文本
        标签名 (str): 要查找的标签名
        属性字典 (dict): 要查找的属性字典，键为属性类型，值为属性值

    返回:
        list: 包含符合条件的元素的列表

    使用示例：
        查找结果 = 通用查找_多个属性(html文本, "div", {"class": "item", "id": "123"})
        print(查找结果)
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        元素列表 = soup.find_all(标签名, 属性字典)
        return 元素列表
    except Exception:
        return []