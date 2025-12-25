from bs4 import BeautifulSoup


def 提取所有p标签(html文本):
    """
    从给定的HTML文本中提取所有的<p>标签，并返回包含这些标签的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有<p>标签的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        p_tags = soup.find_all('p')
        return p_tags
    except Exception:
        return []