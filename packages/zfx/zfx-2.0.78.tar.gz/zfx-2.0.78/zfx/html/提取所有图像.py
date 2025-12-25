from bs4 import BeautifulSoup


def 提取所有图像(html文本):
    """
    从给定的HTML文本中提取所有图像，并返回包含图像URL的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有图像URL的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        图像列表 = [img['src'] for img in soup.find_all('img', src=True)]
        return 图像列表
    except Exception:
        return []