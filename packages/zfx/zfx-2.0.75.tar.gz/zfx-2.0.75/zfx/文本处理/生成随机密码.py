import random
import string


def 生成随机密码(长度, 模式):
    """
    根据给定的长度和模式生成随机密码，确保每种字符类型至少出现一次。

    参数：
        - 长度 (int): 要生成的密码长度。
        - 模式 (int): 生成密码的模式。
            - 1: 只包含数字
            - 2: 数字 + 小写字母
            - 3: 数字 + 小写字母 + 大写字母
            - 4: 数字 + 小写字母 + 大写字母 + 符号
            - 5: 小写字母 + 大写字母
            - 6: 小写字母 + 大写字母 + 符号

    返回值：
        - str: 生成的随机密码。如果发生错误，返回空字符串。

    示例：
        随机密码 = zfx_textutils.生成随机密码(12, 3)
        print(随机密码)  # 输出一个包含数字、小写字母、大写字母的12位密码
    """
    try:
        # 根据模式选择字符集合
        可选字符 = ""
        密码字符 = []

        if 模式 == 1:
            可选字符 = string.digits  # 只包含数字
            密码字符 = [random.choice(可选字符)]  # 确保密码包含数字
        elif 模式 == 2:
            可选字符 = string.digits + string.ascii_lowercase  # 数字 + 小写字母
            密码字符 = [random.choice(string.digits), random.choice(string.ascii_lowercase)]  # 确保包含数字和小写字母
        elif 模式 == 3:
            可选字符 = string.digits + string.ascii_lowercase + string.ascii_uppercase  # 数字 + 小写字母 + 大写字母
            密码字符 = [random.choice(string.digits), random.choice(string.ascii_lowercase), random.choice(string.ascii_uppercase)]  # 确保包含数字、小写字母、大写字母
        elif 模式 == 4:
            可选字符 = string.digits + string.ascii_lowercase + string.ascii_uppercase + string.punctuation  # 数字 + 小写字母 + 大写字母 + 符号
            密码字符 = [random.choice(string.digits), random.choice(string.ascii_lowercase), random.choice(string.ascii_uppercase), random.choice(string.punctuation)]  # 确保包含所有类型的字符
        elif 模式 == 5:
            可选字符 = string.ascii_lowercase + string.ascii_uppercase  # 小写字母 + 大写字母
            密码字符 = [random.choice(string.ascii_lowercase), random.choice(string.ascii_uppercase)]  # 确保包含小写字母和大写字母
        elif 模式 == 6:
            可选字符 = string.ascii_lowercase + string.ascii_uppercase + string.punctuation  # 小写字母 + 大写字母 + 符号
            密码字符 = [random.choice(string.ascii_lowercase), random.choice(string.ascii_uppercase), random.choice(string.punctuation)]  # 确保包含小写字母、大写字母和符号
        else:
            return ""  # 如果模式无效，返回空字符串

        # 计算剩余字符数，并从可选字符中随机选择
        剩余字符数 = 长度 - len(密码字符)
        密码字符 += random.choices(可选字符, k=剩余字符数)

        # 打乱密码字符，确保随机性
        random.shuffle(密码字符)

        # 返回生成的密码
        return ''.join(密码字符)
    except Exception:
        return ""  # 如果发生异常，返回空字符串