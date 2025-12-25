from bs4 import BeautifulSoup


def 提取所有li标签(html文本):
    """
    从给定的HTML文本中提取所有的<li>标签，并返回包含这些标签的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有<li>标签的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        li_tags = soup.find_all('li')
        return li_tags
    except Exception:
        return []