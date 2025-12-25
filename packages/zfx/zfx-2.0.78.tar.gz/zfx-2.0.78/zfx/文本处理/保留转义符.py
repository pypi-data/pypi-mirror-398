def 保留转义符(
    文本: str,
    *,
    使用_repr: bool = False
) -> str:
    """
    保留字符串中的转义符（例如 \n、\t），可选使用 repr() 或 unicode_escape 方式。

    功能说明:
        将输入字符串中可能被 Python 解释为特殊字符的部分（如 \n、\t、\r 等）
        转换为可见的字面形式。开发者可选择:
          - 使用 repr(): 返回带引号的 Python 字面量表示。
          - 使用 unicode_escape: 返回无引号、适合展示或保存的字符串。

    Args:
        文本 (str):
            原始字符串，例如 "abc\\n123" 或 "abc\n123"。
        使用_repr (bool):
            是否使用 repr() 形式输出。
            - True: 返回带引号的 Python 表示形式。
            - False: 返回无引号的转义字符串。
            默认为 False。

    Returns:
        str:
            转换后的字符串。若输入类型错误或转换失败，将返回原始值的字符串形式。

    内部说明:
        - repr() 输出示例: `'fdskljalkrejl\\n213'`
        - unicode_escape 输出示例: `fdskljalkrejl\\n213`
        - 两者差异仅在是否带引号。
    """
    try:
        if 使用_repr:
            return repr(文本)
        return 文本.encode("unicode_escape").decode("utf-8")
    except Exception:
        return str(文本)
