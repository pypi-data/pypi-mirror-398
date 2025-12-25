import re
from typing import Any, List, Tuple


def 筛选_正则保留(序列: List[Any], pattern: str) -> Tuple[List[Any], bool]:
    """
    使用正则表达式从序列中筛选元素（不修改原序列）。

    功能说明:
        - 将序列中每个元素统一转换为字符串，再用正则表达式进行匹配。
        - 使用 re.search()：只要文本中任意位置命中正则规则，就认为匹配成功并保留该元素。
        - pattern 参数是正则表达式字符串，可以实现比普通“包含关键词”更灵活的规则。

        正则表达式常见用法说明（适合小白快速上手）:
            1) 普通文本匹配:
               - pattern = "apple"
                 匹配任意包含 "apple" 这个连续子串的文本。

            2) 开头 / 结尾匹配:
               - pattern = "^abc"
                 匹配以 "abc" 开头的文本（^ 表示开头）。
               - pattern = "xyz$"
                 匹配以 "xyz" 结尾的文本（$ 表示结尾）。

            3) 数字相关:
               - pattern = "\\d+"
                 匹配一个或多个数字（\\d 表示数字，+ 表示至少一次）。
               - pattern = "^\\d{4}-\\d{2}-\\d{2}$"
                 大致匹配 "YYYY-MM-DD" 这种日期格式，例如 2025-12-02。

            4) 多种内容其一（类似 OR）:
               - pattern = "(Xbox|PlayStation)"
                 只要文本中包含 "Xbox" 或 "PlayStation" 之一就算匹配。

            5) 忽略大小写:
               - 可以在 pattern 前加 "(?i)" 开启忽略大小写模式。
                 例如 "(?i)apple" 可以匹配 "apple"、"Apple"、"APPLE" 等。

        实际处理逻辑说明:
            - 先用 re.compile(pattern) 编译正则，提高重复匹配时的效率。
            - 遍历序列中的每个元素，使用 str(元素) 转为字符串。
            - 对每个文本调用 正则.search(文本)：
                · 若返回匹配结果对象，说明命中规则，保留该元素。
                · 若返回 None，说明未命中，丢弃该元素。
            - 最终返回所有命中的元素组成的新列表，原始序列不修改。

    Args:
        序列 (list): 要筛选的原始序列，元素可以是任意类型（数字、字典、字符串等）。
        pattern (str): 正则表达式字符串，用于定义筛选规则。

    Returns:
        list: 只保留正则匹配成功的元素；失败时为空列表。
        bool: 是否成功；成功为 True，失败为 False。
    """
    try:
        正则 = re.compile(pattern)
        结果: List[Any] = []

        for 元素 in 序列:
            文本 = str(元素)
            if 正则.search(文本):
                结果.append(元素)

        return 结果, True

    except Exception:
        return [], False
