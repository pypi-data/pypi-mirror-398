import json


def 格式化json(数据):
    r"""
    功能：
        智能打印格式化的 JSON 数据到控制台：
        - 如果传入的是 Python 对象（dict / list），直接格式化打印；
        - 如果传入的是 JSON 字符串（哪怕一行），先解析再打印。

    参数：
        数据 (str | dict | list):
            - dict / list：已解析好的 Python 对象；
            - str：合法的 JSON 文本。若非合法 JSON，将提示并返回 False。

    内部逻辑：
        1) isinstance 判断是否为 str；
        2) 若为 str，尝试 json.loads 解析；
        3) 使用 json.dumps(indent=4, ensure_ascii=False) 生成格式化文本；
        4) print 输出；
        5) 捕获 TypeError（含不可序列化类型）及其它异常并返回 False。

    返回值：
        bool：打印成功 True；出错 False。

    注意：
        - 只负责打印，不修改输入；
        - 想得到格式化字符串请直接用 json.dumps(数据, indent=4, ensure_ascii=False)；
        - 含 datetime/Decimal/自定义对象时请先转换为基础类型。
    """
    try:
        if isinstance(数据, str):
            try:
                数据 = json.loads(数据)
            except json.JSONDecodeError as e:
                print(f"⚠️ 输入是字符串，但不是有效的 JSON：{e}")
                return False

        格式化文本 = json.dumps(数据, indent=4, ensure_ascii=False)
        print(格式化文本)
        return True

    except TypeError as e:
        print(f"❌ 数据包含无法被序列化的内容: {e}")
        return False
    except Exception as e:
        print(f"❌ 打印时出现异常: {e}")
        return False