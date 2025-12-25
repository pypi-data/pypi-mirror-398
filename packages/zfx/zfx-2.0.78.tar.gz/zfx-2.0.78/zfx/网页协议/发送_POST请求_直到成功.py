import time
import requests
from requests import Response
from typing import Any, Union, Optional


def 发送_POST请求_直到成功(
    url: str,
    间隔秒: float = 3.0,
    严格模式: bool = True,
    最大重试次数: Optional[int] = None,
    **kwargs: Any
) -> Union[Response, str]:
    """
    安全发送 HTTP POST 请求，失败自动重试直到成功（或达到最大重试次数）。

    功能说明：
        封装 requests.post()，在功能上完全兼容原生接口，
        并内置自动重试机制。当请求失败（网络错误、超时、SSL错误、非 2xx 状态码等）时，
        会等待指定间隔后重新尝试，直到请求成功或达到最大重试次数。
        成功返回 Response 对象；失败返回错误信息字符串。
        若未指定最大重试次数，则会无限重试直到成功或人工中断（Ctrl+C）。

    参数：
        url (str):
            请求的完整 URL，例如 "https://www.example.com/api"。
        间隔秒 (float):
            每次失败后的等待间隔秒数，可为小数，默认 3.0。
        严格模式 (bool):
            是否将非 2xx 状态码视为异常。
              - True：状态码非 2xx 视为失败并触发重试。
              - False：无论状态码如何，只要拿到响应即视为成功。
            默认值为 True。
        最大重试次数 (int | None):
            最大重试次数上限（不含首次尝试）。
            例如设为 5，最多共尝试 6 次；
            设为 None 表示无限重试直到成功。
        **kwargs (Any):
            透传给 requests.post() 的任意参数，
            包括 data、json、headers、timeout、proxies、cookies 等。

    返回：
        requests.Response | str:
            - 成功时返回 Response 对象，可直接访问 .text、.json()、.status_code。
            - 达到最大重试次数仍失败时返回错误信息字符串。

    使用示例：
        示例一：无限重试直到成功
            响应 = 发送_POST请求_直到成功(
                "https://www.example.com/api/submit",
                json={"key": "value"},
                timeout=10
            )
            if isinstance(响应, str):
                print("最终失败：", 响应)
            else:
                print("成功：", 响应.status_code)

        示例二：最多重试 5 次，每次间隔 2 秒
            响应 = 发送_POST请求_直到成功(
                "https://www.example.com/api/test",
                data={"id": 123},
                间隔秒=2,
                最大重试次数=5,
                timeout=10
            )
            print("结果：", 响应 if isinstance(响应, str) else 响应.status_code)

    说明：
        1. 适合网络不稳定或需确保请求成功的无人值守任务。
        2. 推荐总是传入 timeout（例如 8~15 秒）避免某次请求长时间卡住。
        3. 若接口长期失败，请检查参数、网络、或服务器可用性。
        4. 若需立即获取响应文本，可在成功后调用 .text。
    """
    尝试次数 = 0
    while True:
        try:
            resp = requests.post(url, **kwargs)
            if 严格模式:
                resp.raise_for_status()
            return resp
        except KeyboardInterrupt:
            return "请求已被手动中断（KeyboardInterrupt）。"
        except Exception as e:
            尝试次数 += 1
            if (最大重试次数 is not None) and (尝试次数 > 最大重试次数):
                return f"请求失败：已重试 {尝试次数} 次仍未成功：{repr(e)}"
            time.sleep(max(0.0, 间隔秒))
