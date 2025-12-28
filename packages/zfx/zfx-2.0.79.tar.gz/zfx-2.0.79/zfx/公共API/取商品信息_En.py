from typing import Any, Dict, List, Optional, Sequence
from concurrent.futures import ThreadPoolExecutor
import base64
import requests


def _b64解码(编码文本: str) -> str:
    """
    内部工具函数：对 Base64 编码的字符串做解码，返回原始明文。

    说明：
        - 仅用于简单“混淆”配置常量，避免在源码里直接明文暴露；
        - 不用于安全加密，懂代码的人依然可以还原内容。
    """
    return base64.b64decode(编码文本).decode("utf-8")


_ENEBA_URL = _b64解码("aHR0cHM6Ly9ncmFwaHFsLmVuZWJhLmNvbS9ncmFwaHFsLw==")

_OPERATION_NAME = _b64解码("V2lja2VkTm9DYWNoZQ==")

_PERSISTED_HASH = _b64解码(
    "ODM0ZGRiNjM5N2I0MmUyNTk3YTc4N2FiNWNiMGE2ZGY5YmZhMzVkYjgxODc2MDE2"
    "ZDk2NjRjMGZlNzQ4ZmM4OF8xNzg1YTAyNGY0NzE3YTYxY2FiZWFmN2U4MTg5YTE3"
    "ZDdiOGY0ODg0NzdlYTYyNDZkMmY5NTNkNDcyNWUwNjM4ZGNlMmZkNDIxOGJhZDFi"
    "OTQ3ZDk1N2Y1N2UyMjA3NGNmNWU5YmI1YmQwMGFkOGE3MDZmNGRhNDVmYzQ0OWEw"
    "ZQ=="
)

_UTM_SOURCE = _b64解码("aHR0cHM6Ly93d3cuZW5lYmEuY29tLw==")


def 获取商品价格列表(slug: str) -> Optional[Dict[str, Any]]:
    """

    功能说明：
        - 请求成功（状态码 200 且返回 JSON）时，返回解析后的 dict 数据；
        - 请求失败、超时或返回非 200 状态码时，返回 None。

    Args:
        slug (str): 商品的 slug 字符串。

    Returns:
        dict | None: 请求成功返回 dict，任何异常或非 200 状态码返回 None。
    """
    url = _ENEBA_URL

    payload = {
        "operationName": _OPERATION_NAME,
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": _PERSISTED_HASH,
            }
        },
        "variables": {
            "currency": "USD",
            "slug": slug,
        },
    }

    for _ in range(3):  # 固定重试 3 次
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass  # 静默处理，继续下一次重试

    # 三次都失败
    return None


def 取商品信息_En(slug序列: Sequence[str]) -> List[Optional[Dict[str, Any]]]:
    """
    功能说明：
        - 若 slug 超过 40 个，不执行请求，直接返回等长的全 None 列表；
        - 返回列表顺序与传入的 slug 序列一一对应；
        - 单个请求失败时，该位置返回 None。

    Args:
        slug序列 (Sequence[str]): slug 序列，长度任意，但超过 40 个则不执行请求。

    Returns:
        list[dict | None]: 每个元素是对应 slug 的接口返回 dict，或 None。
    """
    # 空输入直接返回空列表
    if not slug序列:
        return []

    # 超过 40 个 slug -> 静默失败，全返回 None（长度保持一致）
    if len(slug序列) > 40:
        return [None] * len(slug序列)

    # 线程数量 = slug 数量（上限 40），对 IO 型任务来说完全 OK
    with ThreadPoolExecutor(max_workers=len(slug序列)) as 池:
        结果列表: List[Optional[Dict[str, Any]]] = list(
            池.map(获取商品价格列表, slug序列)
        )

    return 结果列表