from html.parser import HTMLParser
import json
from typing import List, Tuple, Union, Any, Optional


def 解析HTML提取JSON(
        文本: str,
        *,
        只搜_script: bool = True,
        返回原始片段: bool = False,
) -> List[Union[Any, Tuple[Any, str]]]:
    """
    从 HTML 网页源码中自动提取出标准 JSON 数据(不一定适用于所有场景，自行根据实际项目测试后使用)。

    功能说明:
        这个函数的作用是——从一整段网页源码里，把真正的 JSON 数据（例如 `{...}` 或 `[...]`）
        精确地找出来并解析成 Python 对象（字典或列表）。

        它不会用不稳定的正则表达式，而是使用了更可靠的方式：
        1. 先用 HTML 解析器找到所有 `<script>` 标签里的内容；
        2. 再逐个扫描括号 `{}` 和 `[]`，识别出完整的 JSON 结构；
        3. 最后尝试用 `json.loads()` 解析，只有符合标准 JSON 语法的才会被返回。

        这意味着：
        - 像 `window.xxx = {...}` 或 `application/ld+json` 中的数据会被提取；
        - 而函数体、JS 代码、非标准对象（比如单引号包的键名）会被自动忽略；
        - 不会报错，也不会抛异常，最多返回一个空列表。

    Args:
        文本 (str):
            要分析的 HTML 源码。
        只搜_script (bool):
            是否只在 `<script>` 标签里找 JSON。
            如果网页很大，建议保留默认值 True，这样更快更准。
        返回原始片段 (bool):
            如果设为 True，返回结果会同时包含原始 JSON 文本：
                [(解析后的对象, 原始JSON字符串), ...]
            默认只返回 Python 对象（如字典或列表）。

    Returns:
        List[Union[Any, Tuple[Any, str]]]:
            - 提取到的 JSON 数据列表（通常是 dict 或 list）。
            - 如果 `返回原始片段=True`，则会附带原始字符串。
            - 出现任何异常都会自动忽略，函数永远不会抛错，只会返回空列表。

    示例:
        比如网页中有：
            <script>window.__DATA__ = {"id":123,"name":"测试"};</script>
        那么:
            解析HTML提取JSON(网页源码)
        会返回:
            [{'id': 123, 'name': '测试'}]

    提示:
        - 只支持“严格 JSON”格式（双引号、不能有注释、不能有多余逗号）。
        - 如果网页中是宽松格式（如单引号、末尾逗号），函数会自动跳过。
        - 某些网站把 JSON 放在字符串中（如 `JSON.parse("...")`），
          这种情况需要你先手动反转义再交给本函数。
    """

    try:
        # ---------- 内部工具：收集 <script> 文本 ----------
        class _ScriptCollector(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self._in_script = False
                self._buf: Optional[List[str]] = None
                self.scripts: List[str] = []

            def handle_starttag(self, tag: str, attrs) -> None:
                if tag.lower() == "script":
                    self._in_script = True
                    self._buf = []

            def handle_data(self, data: str) -> None:
                if self._in_script and self._buf is not None:
                    self._buf.append(data)

            def handle_endtag(self, tag: str) -> None:
                if tag.lower() == "script":
                    self._in_script = False
                    if self._buf is not None:
                        self.scripts.append("".join(self._buf))
                    self._buf = None

        # ---------- 内部工具：栈式扫描提取候选 JSON 片段 ----------
        def _平衡扫描_提取候选JSON片段(文本块: str) -> List[Tuple[int, int, str]]:
            结果: List[Tuple[int, int, str]] = []
            n = len(文本块)

            栈: List[str] = []
            起点: Optional[int] = None
            处于字符串 = False
            字符串引号: Optional[str] = None  # '"' or "'"
            转义中 = False

            i = 0
            while i < n:
                ch = 文本块[i]

                if 处于字符串:
                    if 转义中:
                        转义中 = False
                    else:
                        if ch == "\\":
                            转义中 = True
                        elif ch == 字符串引号:
                            处于字符串 = False
                            字符串引号 = None
                    i += 1
                    continue

                # 不在字符串里
                if ch == '"' or ch == "'":
                    处于字符串 = True
                    字符串引号 = ch
                    i += 1
                    continue

                if ch == "{" or ch == "[":
                    if not 栈:
                        起点 = i
                    栈.append(ch)
                elif ch == "}" or ch == "]":
                    if 栈:
                        左 = 栈.pop()
                        if (左, ch) not in {("{", "}"), ("[", "]")}:
                            栈.clear()
                            起点 = None
                        elif not 栈 and 起点 is not None:
                            片段 = 文本块[起点:i + 1]
                            结果.append((起点, i + 1, 片段))
                            起点 = None
                    # 孤立右括号直接忽略
                i += 1

            return 结果

        # ---------- 主流程 ----------
        搜索集合: List[str] = []
        if 只搜_script:
            解析器 = _ScriptCollector()
            解析器.feed(文本 or "")
            搜索集合 = [s for s in 解析器.scripts if s] or [文本 or ""]
        else:
            搜索集合 = [文本 or ""]

        命中: List[Union[Any, Tuple[Any, str]]] = []

        for 源 in 搜索集合:
            for _, _, 片段 in _平衡扫描_提取候选JSON片段(源):
                # 只接受严格 JSON：快速前置过滤，减少拿函数体当 JSON 的误报
                s = 片段.lstrip()
                if not (s.startswith('{"') or s.startswith("[")):
                    continue
                try:
                    obj = json.loads(片段)
                except Exception:
                    continue
                命中.append((obj, 片段) if 返回原始片段 else obj)

        return 命中

    except Exception:
        # 任何异常都返回空列表，确保不抛错
        return []