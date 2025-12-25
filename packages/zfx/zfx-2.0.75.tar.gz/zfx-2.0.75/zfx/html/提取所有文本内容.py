from bs4 import BeautifulSoup


def 提取所有文本内容(html文本):
    """
    从给定的HTML文本中提取所有文本内容，并返回一个包含所有文本内容的字符串。

    参数:
        html文本 (str): HTML 文本

    返回:
        str: 包含所有文本内容的字符串
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        文本内容 = soup.get_text()
        return 文本内容.strip()
    except Exception:
        return ""
