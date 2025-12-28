def 微软方式加密邮箱(email):
    """
    模拟微软的方式加密邮箱，显示前两位和最后一位，中间用 "**" 替代。

    参数:
        email (str): 要加密的邮箱地址。

    返回:
        str: 加密后的邮箱地址。如果邮箱格式无效或处理过程中发生异常，则返回空字符串。

    """
    try:
        # 分割邮箱为本地部分和域名部分
        local, domain = email.split("@")

        # 加密本地部分
        if len(local) > 3:
            encrypted_local = local[:2] + "**" + local[-1]
        elif len(local) > 2:
            encrypted_local = local[:2] + "**"
        else:
            encrypted_local = local + "**"

        # 拼接加密后的邮箱
        return f"{encrypted_local}@{domain}"
    except Exception:
        # 返回空字符串表示加密失败
        return ""