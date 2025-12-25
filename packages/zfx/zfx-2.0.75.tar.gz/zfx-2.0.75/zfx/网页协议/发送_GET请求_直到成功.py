import time
import requests
from requests import Response
from typing import Any, Optional, Union


def 发送_GET请求_直到成功(
    url: str,
    间隔秒: float = 3.0,
    严格模式: bool = True,
    最大重试次数: Optional[int] = None,
    **kwargs: Any
) -> Union[Response, str]:
    """
    安全发送 HTTP GET 请求，失败自动重试直到成功（或达到最大重试次数）。

    功能说明：
        在 requests.get() 的基础上封装重试逻辑。
        每次请求失败（网络错误、超时、SSL 错误、状态码异常等）后，等待固定间隔再次重试。
        成功时返回 Response 对象；若达到最大重试次数仍失败，则返回错误信息字符串。
        若未设置最大重试次数（默认 None），将无限次重试，直到成功或被手动中断（Ctrl+C）。

    参数：
        url (str):
            请求的完整 URL，例如 "https://www.example.com"。
        间隔秒 (float):
            每次失败后的等待间隔，单位秒（可为小数），默认 3.0。
        严格模式 (bool):
            是否将非 2xx 状态码视为异常。
              - True：状态码非 2xx 视为失败并触发重试。
              - False：无论状态码，拿到响应即视为成功返回。
            默认值为 True。
        最大重试次数 (int | None):
            最大重试次数上限（不含首次尝试）。例如设为 5，最多共尝试 6 次。
            设为 None 表示无限重试，直到成功或人工中断。
        **kwargs (Any):
            透传给 requests.get() 的所有参数（如 params、headers、timeout、proxies、cookies 等）。

    返回：
        requests.Response | str:
            - 成功：返回 Response 对象（可访问 .text、.json()、.status_code）。
            - 失败：当达到最大重试次数仍未成功时，返回错误信息字符串（包含最后一次异常）。

    使用示例：
        示例一：固定 2 秒重试间隔，无上限重试
            响应 = 发送_GET请求_直到成功("https://www.example.com", 间隔秒=2.0, timeout=10)
            # 如果你没有设置最大重试次数，它会一直重试到成功（或 Ctrl+C）

        示例二：最多重试 5 次，每次间隔 1 秒
            响应 = 发送_GET请求_直到成功(
                "https://www.example.com/api/test",
                间隔秒=1.0,
                最大重试次数=5,
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if isinstance(响应, str):
                print("最终失败：", 响应)
            else:
                print("成功：", 响应.status_code)

    说明：
        1. 建议总是传入 timeout（例如 8~15 秒），避免某次请求长时间卡住。
        2. 若需要自定义“成功”判定（例如必须包含某段文本），可在拿到 Response 后自行验证；
           不满足条件时再手动继续重试或调用本函数再次请求。
        3. 适合无人值守任务：网络偶发抖动时能自动自愈。
    """
    尝试次数 = 0
    while True:
        try:
            resp = requests.get(url, **kwargs)
            if 严格模式:
                resp.raise_for_status()
            return resp
        except KeyboardInterrupt:
            # 尊重人工中断，直接返回错误信息
            return "请求已被手动中断（KeyboardInterrupt）。"
        except Exception as e:
            尝试次数 += 1
            # 达到上限则返回最后一次异常信息
            if (最大重试次数 is not None) and (尝试次数 > 最大重试次数):
                return f"请求失败：已重试 {尝试次数} 次仍未成功：{repr(e)}"
            # 未达到上限则等待后继续
            time.sleep(max(0.0, 间隔秒))