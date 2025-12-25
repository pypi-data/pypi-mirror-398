import os
import configparser


def 读配置项_UTF8(config文件路径: str, 节名称: str, 配置项名称: str, 默认值=None) -> str:
    """
    从以 UTF-8 编码保存的配置文件中读取指定配置项的值。

    参数：
        - config文件路径：配置文件的完整路径。
                         如果配置文件与当前脚本在同一目录下，可仅填写文件名（例如 "config.ini"）。
        - 节名称：要读取的节的名称（例如 'database'）。
        - 配置项名称：要读取的配置项名称（例如 'host'）。
        - 默认值：如果节或配置项不存在，则返回的默认值（默认为 None）。

    返回值：
        - 读取到的配置项字符串值。如果读取失败或不存在，则返回默认值。

    使用示例：
        值 = 读配置项_UTF8('config.ini', 'database', 'host')

    补充说明：
        - 建议使用 UTF-8 编码保存配置文件，以获得更好的跨平台兼容性。
        - 配置文件在脚本同目录下时，只需填写文件名。
    """
    try:
        if not os.path.exists(config文件路径):
            print(f"配置文件不存在：{config文件路径}")
            return 默认值

        config = configparser.ConfigParser()
        config.read(config文件路径, encoding='utf-8')

        if config.has_section(节名称) and config.has_option(节名称, 配置项名称):
            return config.get(节名称, 配置项名称)

        return 默认值

    except Exception as 异常信息:
        print(f"读取配置文件失败：{异常信息}")
        return 默认值