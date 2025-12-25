_enabled = True


def 打印_调试_开启():
    """
    # 多用于调试 开发的时候使用。
    开启全局所有 打印_普通打印() 执行效果
    """
    global _enabled
    _enabled = True


def 打印_调试_关闭():
    """
    # 多用于开发完毕后，关闭打印，避免控制台混乱。
    关闭全局所有 打印_普通打印() 执行效果
    """
    global _enabled
    _enabled = False


def 打印_调试_普通打印(*args, **kwargs):
    """
    AAAAAAAAAAAAA
    此打印方式，受 打印_开启()，打印_关闭() 控制。
    多用于程序开发，中途使用，程序开发完毕，在首部调：用印_关闭() 即可关闭所有的打印效果
    """
    if _enabled:
        print(*args, **kwargs)


def 打印_调试_强制打印(*args, **kwargs):
    """
    此打印方式，不受任何控制。强制执行打印！
    """
    print(*args, **kwargs)
