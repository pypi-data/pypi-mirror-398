import requests
from typing import Any, Optional


def 发送_GET请求_取响应文本(
    url: str,
    严格模式: bool = True,
    **kwargs: Any
) -> Optional[str]:
    """
    安全发送 HTTP GET 请求并返回响应文本。

    功能说明：
        封装 requests.get()，在功能上完全兼容原生接口。
        请求成功时返回响应的文本内容（str）。
        任何异常（超时、网络错误、状态码错误等）均不会抛出异常，而是返回 None。

    参数：
        url (str):
            请求目标的完整 URL，例如 "https://www.example.com"。
        严格模式 (bool):
            是否将非 2xx 状态码视为异常。
              - True：状态码非 2xx 将触发异常并返回 None。
              - False：始终返回响应文本，即使状态码异常。
            默认值为 True。
        **kwargs (Any):
            透传给 requests.get() 的任意参数，
            包括 params、headers、timeout、proxies、cookies 等。

    返回：
        str | None:
            - 请求成功时返回响应文本（HTML、JSON 等）。
            - 请求失败或出现异常时返回 None。

    使用示例：
        示例一：基础请求
            内容 = 发送_GET请求_取响应文本("https://www.example.com")
            if 内容 is None:
                print("请求失败")
            else:
                print("响应内容前100字符：", 内容[:100])

        示例二：带参数与自定义请求头
            内容 = 发送_GET请求_取响应文本(
                "https://www.example.com",
                params={"hl": "en-us", "gl": "US"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            if 内容:
                print("请求成功，长度：", len(内容))
            else:
                print("请求失败")

    说明：
        1. 函数永不抛出异常，适用于批量采集、无人值守或健壮性要求高的场景。
        2. 若需完整 Response 对象，请使用“发送_GET请求()”函数。
        3. 若需自行处理状态码异常，可将严格模式设为 False。
    """
    try:
        resp = requests.get(url, **kwargs)
        if 严格模式:
            resp.raise_for_status()
        return resp.text
    except Exception:
        return None