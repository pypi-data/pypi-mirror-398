import json


def 格式化json_色(数据):
    r"""
    功能：
        智能打印“带缩进、带颜色”的 JSON 数据到控制台：
        - 如果传入的是 Python 对象（dict / list），直接格式化打印；
        - 如果传入的是 JSON 字符串（哪怕一行），先解析再打印；
        - 同一缩进层级的内容使用固定颜色，方便开发者快速分辨层级结构。

    参数：
        数据 (str | dict | list):
            - dict / list：已解析好的 Python 对象；
            - str：合法的 JSON 文本。若非合法 JSON，将提示并返回 False。

    内部逻辑：
        1) isinstance 判断是否为 str；
        2) 若为 str，尝试 json.loads 解析；
        3) 使用 json.dumps(indent=4, ensure_ascii=False) 生成格式化文本；
        4) 按行拆分，通过前导空格数计算缩进层级；
        5) 使用预设的 ANSI 颜色列表，根据层级选择颜色并逐行打印；
        6) 捕获 TypeError（含不可序列化类型）及其它异常并返回 False。

    颜色规则（内部固定，调用方不可配置）：
        - 以缩进层级为索引，在颜色列表中取对应颜色；
        - 层级超过颜色列表长度时，会按列表长度循环取色；
        - 不同缩进层级的行颜色不同，同一层级颜色相同。

    返回值：
        bool：
            - 打印成功：True
            - 解析或序列化出错：False

    注意：
        - 只负责打印，不修改输入；
        - 想得到格式化字符串请直接用 json.dumps(数据, indent=4, ensure_ascii=False)；
        - 含 datetime/Decimal/自定义对象时请先转换为基础类型；
        - 使用 ANSI 颜色码，若终端不支持颜色，则会显示为普通文本的转义字符效果。
    """
    try:
        # 若是字符串，先尝试解析为 JSON
        if isinstance(数据, str):
            try:
                数据 = json.loads(数据)
            except json.JSONDecodeError as e:
                print(f"⚠️ 输入是字符串，但不是有效的 JSON：{e}")
                return False

        # 格式化为带缩进的 JSON 字符串
        格式化文本 = json.dumps(数据, indent=4, ensure_ascii=False)

        # 预设颜色列表：不同层级使用不同颜色（可按喜好调整顺序和色系）
        颜色列表 = [
            "\033[37m",  # 第 0 层：白色
            "\033[36m",  # 第 1 层：青色
            "\033[32m",  # 第 2 层：绿色
            "\033[33m",  # 第 3 层：黄色
            "\033[35m",  # 第 4 层：洋红
            "\033[34m",  # 第 5 层：蓝色
            "\033[90m",  # 第 6 层：灰色
        ]
        颜色重置 = "\033[0m"

        # 按行处理，为每一层加上颜色
        for 行 in 格式化文本.splitlines():
            # 计算前导空格数，根据 indent=4 推导层级
            前导空格数 = len(行) - len(行.lstrip(" "))
            层级 = 前导空格数 // 4 if 前导空格数 > 0 else 0

            # 根据层级选择颜色（层级过大时循环使用颜色）
            颜色 = 颜色列表[层级 % len(颜色列表)]

            # 打印带颜色的行
            print(f"{颜色}{行}{颜色重置}")

        return True

    except TypeError as e:
        print(f"❌ 数据包含无法被序列化的内容: {e}")
        return False
    except Exception as e:
        print(f"❌ 打印时出现异常: {e}")
        return False