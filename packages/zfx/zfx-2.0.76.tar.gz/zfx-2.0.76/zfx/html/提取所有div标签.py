from bs4 import BeautifulSoup


def 提取所有div标签(html文本):
    """
    从给定的HTML文本中提取所有的<div>标签，并返回包含这些标签的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有<div>标签的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        div_tags = soup.find_all('div')
        return div_tags
    except Exception:
        return []
