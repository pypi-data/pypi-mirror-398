from bs4 import BeautifulSoup


def 提取所有标题(html文本):
    """
    从给定的HTML文本中提取所有标题标签，并返回包含标题文本的列表。

    参数:
        html文本 (str): HTML 文本

    返回:
        list: 包含所有标题文本的列表
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        标题列表 = []
        for i in range(1, 7):
            标签名 = f'h{i}'
            标题列表.extend([标题.get_text() for 标题 in soup.find_all(标签名)])
        return 标题列表
    except Exception:
        return []