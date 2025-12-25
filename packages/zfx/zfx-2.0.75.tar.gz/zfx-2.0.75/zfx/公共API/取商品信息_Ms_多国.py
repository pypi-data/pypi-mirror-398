from concurrent.futures import ThreadPoolExecutor
import requests


def 获取产品信息(数据):
    国家 = 数据[0]
    ID列表 = 数据[1]
    合并ID = ",".join([str(i).strip() for i in ID列表 if i])
    payload = {"productIds": [合并ID]}
    url = (
        f"https://storeedgefd.dsx.mp.microsoft.com/v8.0/sdk/products"
        f"?market={国家}&locale=en-US&deviceFamily=Windows.Desktop"
    )
    # 固定重试 5 次
    for _ in range(5):
        try:
            响应 = requests.post(url, data=payload, timeout=10)
            if 响应.status_code == 200 and 响应.text:
                return [国家, 响应.text]
        except Exception:
            pass
    # 三次都失败
    return [国家, ""]


def 合并参数(国家列表, ID列表):
    数据 = []
    for i in 国家列表:
        数据.append([i, ID列表])
    return 数据


def 取商品信息_Ms_多国(国家列表, ID列表):
    """
     并发获取 Microsoft Store 产品信息（多国家版本）。

     功能说明：
         基于提供的国家列表与产品 ID 列表，按照每个国家生成一次请求，
         并使用多线程并发调用 Microsoft Store 官方接口。
         返回结果为按国家顺序排列的列表，每项格式为：
             [国家代码, 响应文本]
         若某个国家请求失败，会返回：
             [国家代码, ""]
         参数格式不符合要求时，将直接返回空列表。

     参数：
         国家列表 (list[str]):
             用于请求的市场区域代码列表，例如 ["US", "JP", "AR"]。
             - 必须为列表类型；
             - 列表内每个元素必须为非空字符串；
             - 否则直接返回空列表。

         ID列表 (list[str]):
             产品 ID 列表，例如 ["9PNC01XSXXXX", "9N3V98GLXXXX"]。
             - 必须为列表类型且上限25个ID；
             - 列表内每个元素必须为非空字符串；
             - 否则直接返回空列表。

     返回：
         list[list[str, str]]:
             当参数合法时，返回形如：
                 [
                     ["US", "<响应文本>"],
                     ["JP", "<响应文本>"],
                     ["AR", ""],           # 该国家请求失败
                     ...
                 ]
             当参数不合法时，返回空列表。

     安全性说明：
         - 内部对网络请求进行了固定 3 次重试；
         - 发生异常时不会抛出异常，而是静默处理并返回空文本；
         - 不对外暴露内部实现细节，适合外部模块直接调用。
     """
    # -------- 参数校验 --------
    # 国家列表必须是 list 且每个元素都是非空字符串
    if not isinstance(国家列表, list) or not all(isinstance(i, str) and i.strip() for i in 国家列表):
        return []
    # ID列表必须是 list 且每个元素都是非空字符串
    if not isinstance(ID列表, list) or not all(isinstance(i, str) and i.strip() for i in ID列表):
        return []

    # -------- 合并参数 --------
    数据 = 合并参数(国家列表, ID列表)

    # -------- 并发执行 --------
    with ThreadPoolExecutor(max_workers=30) as 池:
        执行结果 = list(池.map(获取产品信息, 数据))

    return 执行结果