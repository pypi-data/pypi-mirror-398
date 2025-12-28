def 取首行无标记文本S(文件路径, 标记列表):
    r"""
    功能：
        从账号记录文本中读取第一行未包含任意标记字符串的账号信息，并返回其所在行号。

    用途场景：
        支持批处理账号文本，按多种标记（如“已完成”、“跳过”、“无效”等）过滤处理过的行。

    参数：
        - 文件路径: 账号记录文本文件的路径。
        - 标记列表: 一个包含多个标记字符串的列表，例如 ["已完成", "跳过"]。

    返回值：
        - 成功时：返回一个元组 (行号, 行内容)，行号从 1 开始计。
        - 所有账号均已标记：返回 None。
        - 打开或读取文件失败：返回 False。

    注意事项：
        1. 文件需为 UTF-8 编码格式。
        2. 任意标记字符串只要出现在行内，即视为已处理。
        3. 返回的行号便于定位或更新该行。

    使用示例：
        假设“accounts.txt”文件内容如下：
            - user1----pass1----token1----已完成
            - user2----pass2----token2----跳过
            - user3----pass3----token3
            - user4----pass4----token4----无效

        示例代码：
            文件路径 = "accounts.txt"
            标记列表 = ["已完成", "跳过", "无效"]
            结果 = 取首行无标记文本S(文件路径, 标记列表)

            if isinstance(结果, tuple):
                行号, 内容 = 结果
                print(f"第 {行号} 行账号信息：{内容}")
            elif 结果 is None:
                print("所有账号均已标记")
            else:
                print("读取失败")
    """
    try:
        with open(文件路径, 'r', encoding='utf-8') as 文件对象:
            for 索引, 行内容 in enumerate(文件对象, start=1):
                当前行 = 行内容.rstrip('\n').rstrip('\r')
                if not any(标记 in 当前行 for 标记 in 标记列表):
                    return 索引, 当前行
        return None
    except Exception:
        return False
