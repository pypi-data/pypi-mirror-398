def 字符串替换(源字符串, 要替换的旧子串, 替换为的新子串):
    """
    将字符串中的指定子串替换为新子串。

    参数:
        - 源字符串 (str): 要进行替换操作的源字符串。
        - 要替换的旧子串 (str): 要被替换的子串。
        - 替换为的新子串 (str): 替换后的新子串。

    返回:
        - str: 替换完成后的字符串，如果出现任何异常，则返回 None。

    示例:
        源字符串 = "Hello, World!"
        替换后的字符串 = zfx_textutils.字符串替换(源字符串, "World", "Universe")
        print("替换后的字符串:", 替换后的字符串)  # 输出: Hello, Universe!
    """
    try:
        替换后的字符串 = 源字符串.replace(要替换的旧子串, 替换为的新子串)
        return 替换后的字符串
    except Exception:
        return None