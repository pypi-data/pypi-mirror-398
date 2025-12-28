import requests
from typing import Any


def 发送_POST请求_取响应文本(
    url: str,
    严格模式: bool = True,
    **kwargs: Any
) -> str:
    """
    安全发送 HTTP POST 请求并直接返回响应文本。
    如果请求成功则返回响应内容（字符串），如果请求失败则返回错误信息字符串，
    所以无需判断类型即可直接使用字符串结果。

    功能说明：
        封装 requests.post()，在功能上完全兼容原生接口，
        但在出现异常（网络错误、超时、SSL错误等）时不会抛出异常，
        而是返回错误信息字符串。可选“严格模式”控制状态码判断。
        与“发送_POST请求”不同，本函数直接返回响应文本（str）。

    参数：
        url (str):
            请求的完整 URL，例如 "https://www.example.com/api"。
        严格模式 (bool):
            是否将非 2xx 状态码视为异常。
              - True：状态码非 2xx 将触发异常并返回错误信息。
              - False：始终返回响应文本。
            默认值为 True。
        **kwargs (Any):
            透传给 requests.post() 的任意参数，
            包括 data、json、headers、timeout、proxies、cookies 等。

    返回：
        str:
            - 请求成功（或严格模式关闭）时返回响应文本（HTML、JSON等内容字符串）。
            - 出现任何异常时返回错误信息字符串，如 "请求失败: 连接超时"。

    使用示例：
        示例一：发送表单数据并取文本
            文本 = 发送_POST请求_取响应文本(
                "https://www.example.com/api/login",
                data={"username": "admin", "password": "123456"},
                timeout=10
            )
            print(文本[:200])

        示例二：发送 JSON 数据
            文本 = 发送_POST请求_取响应文本(
                "https://www.example.com/api/submit",
                json={"task": "run", "priority": "high"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            if 文本.startswith("请求失败:"):
                print("失败：", 文本)
            else:
                print("成功，响应长度：", len(文本))

    说明：
        1. 可替代原生 requests.post() 安全使用；
           无论何种异常均不会抛出错误。
        2. 适用于只关心文本内容、不需要 Response 对象的场景。
        3. 若需 JSON 请求体，请使用 json=payload 而非 data=payload。
        4. 若需完整 Response 对象，请使用“发送_POST请求”。
    """
    try:
        resp = requests.post(url, **kwargs)
        if 严格模式:
            resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"请求失败: {repr(e)}"