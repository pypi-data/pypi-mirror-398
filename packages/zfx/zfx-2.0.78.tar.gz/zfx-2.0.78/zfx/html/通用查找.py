from bs4 import BeautifulSoup


def 通用查找(html文本, 标签名, 属性类型, 属性值):
    """
    从给定的HTML文本中，根据标签名和单个属性中包含的多个属性值查找元素，并返回包含这些元素的列表。

    参数:
        html文本 (str): HTML 文本
        标签名 (str): 要查找的标签名（例如，a、p、div、span、img、ul、ol、li、table、tr、td、th、form、input、button、label、header、等等更多）
        属性类型 (str): 要查找的属性类型（例如，class、id、name 等）
        属性值 (str): 要查找的属性值，可以包含多个值，用空格隔开

    返回:
        list: 包含符合条件的元素的列表

    示例：
        查找结果 = 通用查找_单属性多值匹配(响应文本, "div", "class", "MPoNoS d3kAJw")
        print(查找结果)
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        属性值列表 = 属性值.split()
        匹配元素列表 = soup.find_all(标签名)

        临时元素列表 = []
        for 元素 in 匹配元素列表:
            for 属性, 值 in 元素.attrs.items():
                if 属性 == 属性类型:
                    if isinstance(值, str):
                        值列表 = 值.split()
                        if all(item in 值列表 for item in 属性值列表):
                            临时元素列表.append(元素)
                            break
                    elif isinstance(值, list):
                        if all(item in 值 for item in 属性值列表):
                            临时元素列表.append(元素)
                            break

        return 临时元素列表
    except Exception:
        return []