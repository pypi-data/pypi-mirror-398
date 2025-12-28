import requests
from typing import List, Dict, Optional


def 取商品信息_Ms(国家: str, 语言: str, ID列表: List[str]) -> Optional[Dict]:
    """
    从 Microsoft Store 官方服务接口获取产品信息（StoreEdgeFD 后端接口）。

    功能说明:
        通过 POST 请求一次性获取多个产品的详细信息（如标题、描述、价格、可售状态等）。
        本函数接收标准 Python 列表格式的产品ID（如 ["AAA", "BBB", "CCC"]），
        并在内部自动将其拼接为微软要求的特殊格式：
            {"productIds": ["AAA,BBB,CCC"]}
        即 “单元素列表，元素为逗号分隔的 ID 字符串”。
        该接口常用于 Microsoft Store 商店内部通信，返回结构体较大且层级较深。

    参数:
        国家 (str):
            市场区域代码（market），如:
                - "US"（美国）
                - "CN"（中国）
                - "JP"（日本）
                - "BR"（巴西）
                - "TR"（土耳其）
        语言 (str):
            语言区域代码（locale），如:
                - "en-US"（英语-美国）
                - "zh-CN"（中文-简体）
                - "ja-JP"（日语）
                - "pt-BR"（葡萄牙语-巴西）
        产品ID列表 (List[str]):
            标准 Python 列表形式的产品 ID 集合，例如:
                ["9PKT24SXQGPD", "9NBLGGH4R315"]
            - 列表长度范围为 1~25。
            - 函数内部会自动拼接为 "AAA,BBB,CCC" 格式后再封装为单元素列表提交。

    返回:
        dict | None:
            - 成功: 返回完整 JSON 响应数据（通常顶层包含 "Products"）。
            - 失败: 返回 None。

    注意事项:
          本功仅用作学习、测试用途，请勿运用于实际项目中，否则自行承风险及后果。
        - 若返回错误或空值，请检查:
            * ID 数量是否超过 25；
            * 是否使用了正确的格式；
            * market/locale 是否匹配；
            * 是否存在访问区域限制。

    ⚠️ 免责声明:
        本函数仅供个人学习与研究使用，禁止商业化或公开分发。
        本函数调用的接口 (storeedgefd.dsx.mp.microsoft.com) 为 Microsoft Store
        客户端使用的后端通信端点，目前**未在微软公开文档中列为正式 API**。
        其返回结构、访问权限及可用性可能随系统或地区变化。
        使用该接口需了解以下风险:
            - 接口可能在未来版本中变更、调整或被关闭；
            - 微软未对该接口的第三方使用提供支持或授权；
            - 若用于生产或商业用途，可能违反 Microsoft Store 的服务条款；
            - 建议仅限于学习、研究或非商业的数据分析用途。

    示例:
        取商品信息_Ms("US", "en-US", ["AAAAAAA", "BBBBBBB"])
    """
    try:
        if not isinstance(ID列表, list) or not ID列表:
            raise ValueError("产品ID列表必须是非空的列表。")
        if len(ID列表) > 25:
            raise ValueError("每次请求的产品ID数量不能超过25个。")

        合并ID = ",".join([str(i).strip() for i in ID列表 if i])
        payload = {"productIds": [合并ID]}

        url = (
            f"https://storeedgefd.dsx.mp.microsoft.com/v8.0/sdk/products"
            f"?market={国家}&locale={语言}&deviceFamily=Windows.Desktop"
        )

        响应 = requests.post(url, data=payload, timeout=10)
        if 响应.status_code == 200:
            return 响应.json()
        return None
    except Exception:
        return None
