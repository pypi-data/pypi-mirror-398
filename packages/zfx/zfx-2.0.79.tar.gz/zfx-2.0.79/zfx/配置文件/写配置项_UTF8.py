import os
import configparser


def 写配置项_UTF8(config文件路径: str, 节名称: str, 配置项名称: str, 值) -> bool:
    """
    将指定的配置项写入到以 UTF-8 编码保存的配置文件中。

    参数：
        - config文件路径：配置文件的完整路径。
                         如果配置文件与当前脚本在同一目录下，可仅填写文件名（例如 "config.ini"）。
        - 节名称：要写入的节的名称（例如 'database'）。
        - 配置项名称：要写入的配置项名称（例如 'host'）。
        - 值：要写入的值，会自动转换为字符串。

    返回值：
        - 写入成功返回 True。
        - 写入失败返回 False，并打印错误信息。

    使用示例：
        写配置项_UTF8('config.ini', 'database', 'host', 'localhost')

    补充说明：
        - 如果配置文件与当前脚本位于同一目录，只需填写文件名即可，无需写绝对路径。
        - 写入时使用 UTF-8 编码，推荐在跨平台环境（Windows / Linux）中使用。
    """
    try:
        if not os.path.exists(config文件路径):
            print(f"配置文件不存在：{config文件路径}，将自动创建新文件。")

        config = configparser.ConfigParser()
        config.read(config文件路径, encoding='utf-8')

        if not config.has_section(节名称):
            config.add_section(节名称)

        config.set(节名称, 配置项名称, str(值))

        with open(config文件路径, 'w', encoding='utf-8') as 文件:
            config.write(文件)

        return True

    except Exception as 异常信息:
        print(f"写入配置文件失败：{异常信息}")
        return False