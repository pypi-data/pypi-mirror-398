import re
import json


def 提取所有字典(html文本):
    """
    从 HTML 文本中提取所有的 JSON 字典。

    参数:
        - html文本 (str): 包含 HTML 内容的字符串。

    返回:
        - json字典列表 (list): 提取出的所有 JSON 字典的列表。
    """
    try:
        # 确保 html文本 是字符串类型
        html文本 = str(html文本)

        # 匹配所有的 JSON 字典
        json字典列表 = []
        pattern = re.compile(r'\{.*?\}', re.DOTALL)
        matches = pattern.findall(html文本)

        # 尝试将匹配到的内容解析为 JSON
        for match in matches:
            try:
                json字典 = json.loads(match)
                json字典列表.append(json字典)
            except json.JSONDecodeError:
                continue

        return json字典列表
    except Exception:
        return []