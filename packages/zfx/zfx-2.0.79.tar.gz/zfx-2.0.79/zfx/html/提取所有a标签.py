from bs4 import BeautifulSoup


def 提取所有a标签(html文本):
    """
    从给定的HTML文本中提取所有的<a>标签，并返回包含这些标签的列表。

    参数:
        html_text (str): HTML 文本

    返回:
        list: 包含所有<a>标签的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        a_tags = soup.find_all('a')
        return a_tags
    except Exception:
        return []