import subprocess


def NAME_终止进程(进程名, debug=True):
    """
    尝试通过进程名称终止所有匹配的进程（仅适用于 Windows 系统）。

    参数:
        - 进程名 (str): 要终止的进程名称，包括扩展名（如 chrome.exe）。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - bool:
            - 所有进程终止成功返回 True；
            - 如未找到进程或终止失败则返回 False。

    注意事项:
        1. 本函数使用系统命令 tasklist + taskkill 实现，仅支持 Windows。
        2. 本函数适用于需要一次性结束某类进程的场景。
        3. 本函数不依赖 psutil 模块。

    使用示例:
        状态 = NAME_终止进程("chrome.exe")
        状态 = NAME_终止进程("notepad.exe", debug=False)
    """
    try:
        result = subprocess.run(['tasklist', '/fi', f'imagename eq {进程名}'], capture_output=True, text=True)
        if 进程名.lower() not in result.stdout.lower():
            return False

        kill_result = subprocess.run(['taskkill', '/f', '/im', 进程名], capture_output=True, text=True)
        return kill_result.returncode == 0
    except Exception as e:
        if debug:
            print(f"[NAME_终止进程] 异常：{e} (进程名={进程名})")
        return False
