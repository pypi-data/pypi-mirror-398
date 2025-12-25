import getpass


def 取用户名():
    """
    获取当前系统用户名。

    返回:
        str: 当前系统用户名。如果获取失败，则返回 None。

    使用示例:
        current_username = 系统_取用户名()
        print("当前系统用户名:", current_username)
    """
    try:
        username = getpass.getuser()
        return username
    except Exception:
        return None
