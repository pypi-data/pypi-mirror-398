import poplib


def 登录(服务器地址, 用户名, 密码):
    """
    尝试连接到指定的 POP3 服务器并登录邮箱账户（仅支持使用 110 端口的非加密协议）。

    参数：
        - 服务器地址 (str)：POP3 服务器的地址，例如 'pop.服务器.com'。
        - 用户名 (str)：邮箱账户的用户名。
        - 密码 (str)：邮箱账户的密码。

    返回值：
        - poplib.POP3：如果登录成功，返回连接成功的 POP3 服务器对象。
        - bool：如果登录失败或出现异常，返回 False。

    使用示例：
        邮件服务器 = zfx_pop3.登录('pop.服务器.com', '用户名', '密码')
        if 邮件服务器:
            print("登录成功")
        else:
            print("登录失败")

    注意：
        - 此函数仅支持未加密的 POP3 协议（端口 110）。如果需要加密连接，请使用 POP3_SSL 或者其他安全协议。
        - 调用者应在完成所有操作后调用 `zfx_pop3.断开连接(邮件服务器)` 以关闭会话。
    """
    try:
        # 连接到 POP3 服务器（110 端口，非加密）
        邮件服务器 = poplib.POP3(服务器地址, 110)

        # 尝试使用用户名和密码登录
        响应用户 = 邮件服务器.user(用户名)
        响应密码 = 邮件服务器.pass_(密码)

        # 判断是否成功登录
        if 响应用户.startswith(b'+OK') and 响应密码.startswith(b'+OK'):
            return 邮件服务器  # 返回成功连接的 POP3 服务器对象
        else:
            return False  # 登录失败
    except Exception:
        return False  # 捕获异常并返回 False