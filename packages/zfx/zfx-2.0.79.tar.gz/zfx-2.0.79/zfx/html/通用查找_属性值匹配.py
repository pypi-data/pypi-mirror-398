from bs4 import BeautifulSoup


def 通用查找_属性值匹配(html文本, 属性值):
    """
    从给定的HTML文本中查找所有属性值匹配的元素（匹配所有标签和所有属性类型），并返回包含这些元素的列表。

    参数:
        html文本 (str): HTML 文本
        属性值 (str): 要查找的属性值，可以包含多个值，用空格隔开

    返回:
        list: 包含符合条件的元素的列表

    示例：
        查找结果 = 通用查找_属性值匹配(响应文本, "ZPGj85")
        print(查找结果)
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        属性值列表 = 属性值.split()
        元素列表 = []

        # 遍历所有元素
        for 元素 in soup.find_all(True):
            # 遍历元素的所有属性，检查是否有属性值匹配
            for 属性, 值 in 元素.attrs.items():
                if isinstance(值, list):
                    if all(属性值 in 值 for 属性值 in 属性值列表):
                        元素列表.append(元素)
                        break
                elif isinstance(值, str):
                    值列表 = 值.split()
                    if all(属性值 in 值列表 for 属性值 in 属性值列表):
                        元素列表.append(元素)
                        break

        return 元素列表
    except Exception:
        return []