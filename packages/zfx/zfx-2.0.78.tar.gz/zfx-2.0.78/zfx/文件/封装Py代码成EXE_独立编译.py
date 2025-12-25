import subprocess
import os
import sys
import tempfile


def 封装Py代码成EXE_独立编译(脚本路径):
    """
    将指定的 Python 脚本打包成可执行的 EXE 文件，并将输出文件保存到桌面。

    参数：
        - 脚本路径：要打包的 Python 脚本的路径，应该指向一个有效的 Python 脚本文件。

    返回值：
        - 无

    异常：
        - subprocess.CalledProcessError：如果打包过程中出现错误，将会抛出 CalledProcessError 异常。
        - FileNotFoundError：如果找不到 pyinstaller.exe，抛出异常并提示错误。

    注意事项：
        1. 该函数会将指定的 Python 脚本封装成 EXE 文件。
        2. 打包后的 EXE 文件将会保存在用户的桌面上。
        3. 使用 `--onefile` 参数将生成单个 EXE 文件。

    使用示例：
        脚本路径 = "/path/to/script.py"
        封装Py代码成EXE_独立编译(脚本路径)
    """
    try:
        # 获取系统桌面的路径
        桌面路径 = os.path.join(os.path.expanduser("~"), 'Desktop')

        # 获取当前 Python 环境下 pyinstaller 的路径
        pyinstaller_path = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pyinstaller.exe')

        # 检查 pyinstaller 是否存在
        if not os.path.isfile(pyinstaller_path):
            raise FileNotFoundError(f"无法找到 pyinstaller.exe，请确保已安装 PyInstaller。")

        # 创建一个临时目录
        with tempfile.TemporaryDirectory() as 临时目录:
            # 使用 subprocess.run 调用 pyinstaller 命令，将脚本打包成单个 EXE 文件，并指定输出目录为桌面
            subprocess.run([pyinstaller_path, '--onefile', '--distpath', 桌面路径, '--workpath', 临时目录, '--specpath', 临时目录, 脚本路径], check=True)

        print(f"成功将 {脚本路径} 打包成 EXE 文件，并保存在桌面。")  # 打包成功后输出提示信息
    except subprocess.CalledProcessError as e:
        # 如果打包过程中发生错误，捕获异常并输出错误信息
        print(f"打包过程中出现错误: {e}")
    except FileNotFoundError as e:
        # 如果无法找到 pyinstaller.exe，捕获并输出错误信息
        print(e)