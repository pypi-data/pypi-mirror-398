def 获取邮件数量(服务器对象):
    """
    获取邮箱中的邮件数量。

    参数：
        - 服务器对象 (poplib.POP3)：已经连接并登录的 POP3 服务器对象。

    返回值：
        - int：邮箱中的邮件数量。
        - bool：如果获取过程中发生异常，返回 False。

    使用示例：
        邮件服务器 = zfx_pop3.登录('pop.服务器.com', '用户名', '密码')
        邮件数量 = zfx_pop3.获取邮件数量(邮件服务器)
        if 邮件数量 is not False:
            print(f"邮箱中共有 {邮件数量} 封邮件")
        else:
            print("获取邮件数量失败")

    注意：
        - 此函数返回邮箱中的邮件总数，如果发生异常，则返回 False。
    """
    try:
        # 获取邮箱中的邮件数量和总大小
        邮件数量, _ = 服务器对象.stat()
        return 邮件数量  # 返回邮件数量
    except Exception:
        return False  # 捕获异常并返回 False