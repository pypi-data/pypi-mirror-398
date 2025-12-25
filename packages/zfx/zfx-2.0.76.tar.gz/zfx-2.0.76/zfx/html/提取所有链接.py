from bs4 import BeautifulSoup


def 提取所有链接(html文本):
    """
    从给定的HTML文本中提取所有链接，并返回包含链接URL的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有链接URL的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        链接列表 = [a['href'] for a in soup.find_all('a', href=True)]
        return 链接列表
    except Exception:
        return []