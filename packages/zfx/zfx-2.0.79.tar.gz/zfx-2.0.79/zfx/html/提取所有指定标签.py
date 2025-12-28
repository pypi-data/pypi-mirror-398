from bs4 import BeautifulSoup


def 提取所有指定标签(html文本, 标签名):
    """
    从给定的HTML文本中提取所有指定的标签，并返回包含这些标签的列表。

    参数:
        html文本 (str): HTML 文本
        标签名 (str): 要提取的标签名

    返回:
        list: 包含所有指定标签的列表

    常用标签名示例:
        - 'a': 超链接
        - 'p': 段落
        - 'div': 区块
        - 'span': 行内区块
        - 'img': 图像
        - 'ul': 无序列表
        - 'ol': 有序列表
        - 'li': 列表项
        - 'table': 表格
        - 'tr': 表格行
        - 'td': 表格单元格
        - 'th': 表格表头
        - 'form': 表单
        - 'input': 输入框
        - 'button': 按钮
        - 'label': 标签
        - 'header': 页头
        - 'footer': 页脚
        - 'nav': 导航
        - 'section': 章节
        - 'article': 文章
        - 'aside': 旁注内容
        - 'iframe': 内联框架
        - 'h1', 'h2', 'h3', 'h4', 'h5', 'h6': 标题
        - 'meta': 元数据
        - 'link': 链接到外部资源
        - 'script': 脚本
    """
    try:
        soup = BeautifulSoup(html文本, 'html.parser')
        标签列表 = soup.find_all(标签名)
        return 标签列表
    except Exception:
        return []