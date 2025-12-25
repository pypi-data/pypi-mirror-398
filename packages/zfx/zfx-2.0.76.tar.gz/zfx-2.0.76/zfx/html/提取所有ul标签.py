from bs4 import BeautifulSoup


def 提取所有ul标签(html文本):
    """
    从给定的HTML文本中提取所有的<ul>标签，并返回包含这些标签的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有<ul>标签的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        ul_tags = soup.find_all('ul')
        return ul_tags
    except Exception:
        return []