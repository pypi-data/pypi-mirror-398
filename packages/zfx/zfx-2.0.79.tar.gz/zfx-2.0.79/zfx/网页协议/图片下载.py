import requests
import os
import shutil


def 图片下载(图片链接, 保存目录, 图片名称):
    """
    功能：
        从指定的 URL 下载图片，并保存到本地目录下指定文件名。
        如果目录不存在，会自动创建。

    参数：
        - 图片链接 (str)：
            图片的网络地址，例如 "https://www.example.com/image.png"。
        - 保存目录 (str)：
            本地保存路径，例如 r"C:\\tmp"。
        - 图片名称 (str)：
            保存的文件名，例如 "download.png"。

    返回：
        - bool：
            下载并保存成功返回 True；
            下载失败或出现异常时返回 False。

    异常处理逻辑：
        - 如果目录创建失败、网络请求失败、文件写入失败等情况，返回 False。

    示例：
        >>> 链接 = "https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"
        >>> 目录 = r"C:\\tmp"
        >>> 文件名 = "baidu.png"
        >>> 成功 = 图片下载(链接, 目录, 文件名)
        >>> print(成功)
        True

    注意事项：
        - 本函数只简单判断状态码 == 200，未对 Content-Type 做校验。
        - 使用 `stream=True` 可以避免一次性加载整个文件到内存，更适合下载大文件。
        - 如果保存路径下已有同名文件，会被覆盖。
    """
    try:
        # 确保保存目录存在
        os.makedirs(保存目录, exist_ok=True)

        # 构造完整路径
        文件路径 = os.path.join(保存目录, 图片名称)

        # 发送 GET 请求
        response = requests.get(图片链接, stream=True)

        if response.status_code == 200:
            with open(文件路径, 'wb') as file:
                shutil.copyfileobj(response.raw, file)
            return True
        return False
    except Exception:
        return False
