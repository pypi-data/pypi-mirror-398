import subprocess
import os
import sys
import tempfile


def 封装代码_独立编译(脚本路径, 隐藏导入模块=None):
    """
    将指定的 Python 脚本打包成独立 EXE 可执行文件（--onefile 模式），并输出到用户桌面。

    参数：
        - 脚本路径：要打包的 Python 脚本的完整路径，例如 "D:\\项目\\主程序.py"。
        - 隐藏导入模块：可选参数，列表形式，用于指定 PyInstaller 打包时需要显式声明的模块依赖。
            - 示例：["mysql.connector.plugins.mysql_native_password", "selenium"]
            - 适用于某些模块在运行时动态导入，PyInstaller 静态分析无法识别时。

    返回值：
        - 无。打包成功后，EXE 文件将输出到桌面。
        - 若参数错误或打包失败，将在控制台输出详细错误提示信息，不抛出异常。

    注意事项：
        1. 本函数使用 PyInstaller 将 Python 脚本封装为单个 EXE 文件（--onefile 模式）。
        2. 请确保系统中已正确安装 PyInstaller，否则将提示路径不存在。
        3. 若脚本依赖的模块为动态导入，请通过 `隐藏导入模块` 参数显式添加。
        4. 打包结果为单个独立的可执行文件，适用于无资源依赖的部署环境。

    使用示例：
        脚本路径 = "D:\\项目\\主程序.py"
        隐藏模块 = ["mysql.connector.plugins.mysql_native_password"]
        封装代码_独立编译(脚本路径, 隐藏模块)

        输出路径示例：
        C:\\Users\\你的用户名\\Desktop\\主程序.exe
    """
    桌面路径 = os.path.join(os.path.expanduser("~"), 'Desktop')
    pyinstaller_path = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pyinstaller.exe')

    # 检查 PyInstaller 是否存在
    if not os.path.isfile(pyinstaller_path):
        print(f"❌ 错误：未找到 pyinstaller.exe，请确认已正确安装。\n路径: {pyinstaller_path}")
        return

    # 参数类型检查
    if 隐藏导入模块 is not None:
        if not isinstance(隐藏导入模块, (list, tuple)) or not all(isinstance(m, str) for m in 隐藏导入模块):
            print("❌ [类型错误] 隐藏导入模块参数必须是字符串列表，例如：['模块1', '模块2']")
            return

    try:
        with tempfile.TemporaryDirectory() as 临时目录:
            命令 = [
                pyinstaller_path,
                '--onefile',
                '--distpath', 桌面路径,
                '--workpath', 临时目录,
                '--specpath', 临时目录
            ]

            if 隐藏导入模块:
                for 模块名 in 隐藏导入模块:
                    命令.append(f'--hidden-import={模块名}')

            命令.append(脚本路径)

            print(f"🚀 正在打包：{os.path.basename(脚本路径)}")
            subprocess.run(命令, check=True)
            print(f"✅ 打包成功：{os.path.basename(脚本路径)} 已输出至桌面。")

    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败（PyInstaller 出错）\n错误信息：{e}")
    except Exception as e:
        print(f"❌ 发生未知错误：{e}")
