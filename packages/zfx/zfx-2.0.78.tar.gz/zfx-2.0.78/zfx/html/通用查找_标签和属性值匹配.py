from bs4 import BeautifulSoup


def 通用查找_标签和属性值匹配(html文本, 标签名, 属性值):
    """
    从给定的HTML文本中，根据标签名查找所有属性值匹配的元素（会匹配所有的属性类型），并返回包含这些元素的列表。

    参数:
        html文本 (str): HTML 文本
        标签名 (str): 要查找的标签名（例如，a、p、div、span、img、ul、ol、li、table、tr、td、th、form、input、button、label、header、等等更多）
        属性值 (str): 要查找的属性值，可以包含多个值，用空格隔开

    返回:
        list: 包含符合条件的元素的列表

    示例：
        # 查找结果 = 通用查找_标签和属性值匹配(响应文本, "div", "d-table-row rating individual-rating")
        查找结果 = 通用查找_标签和属性值匹配(响应文本, "div", "d-table-row")
        print(查找结果)
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        属性值列表 = 属性值.split()
        匹配元素列表 = soup.find_all(标签名)

        for 属性值 in 属性值列表:
            临时元素列表 = []
            for 元素 in 匹配元素列表:
                for 属性, 值 in 元素.attrs.items():
                    if isinstance(值, list):
                        if 属性值 in 值:
                            临时元素列表.append(元素)
                            break
                    elif isinstance(值, str):
                        if 属性 == 'class':
                            if 属性值 in 值.split():
                                临时元素列表.append(元素)
                                break
                        else:
                            if 属性值 == 值:
                                临时元素列表.append(元素)
                                break
            匹配元素列表 = 临时元素列表

        return 匹配元素列表
    except Exception:
        return []
