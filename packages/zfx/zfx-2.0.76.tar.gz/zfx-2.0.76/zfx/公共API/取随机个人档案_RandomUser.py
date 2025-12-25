import requests


def 取随机个人档案_RandomUser() -> dict | None:
    """
    获取随机个人档案的**原始 JSON**数据（randomuser.me，Cloudflare 全球 CDN 托管）。

    功能说明:
        - 通过 HTTPS 请求 `https://randomuser.me/api/`，直接返回接口的**完整原始 JSON** 数据结构，不做任何字段裁剪、
          重命名、类型转换或二次解析，便于上层调用者自行处理。
        - 该服务用于生成**虚拟测试数据**（并非真实个人），常用于 UI 占位、表单测试、自动化脚本模拟等。
        - 服务由 Cloudflare 全球节点加速，长期可用、延迟低、稳定性高；默认无需认证与密钥，合理调用即可。

    返回数据结构（官方典型示例，字段可能随版本有增减）:
        顶层:
            - results (list[dict]): 随机人物列表（默认 1 条）。本函数**不**从中取第一条，而是返回整个 JSON。
            - info (dict): 请求附加信息（如 seed、results、page、version）。
        results[i] 典型字段（并非完整列表；具体以实际返回为准）:
            - gender (str): 性别，"male" / "female"。
            - name (dict):
                - title (str): 称谓（如 "Mr"、"Mrs"）。
                - first (str): 名。
                - last  (str): 姓。
            - location (dict):
                - street (dict): { number (int), name (str) }
                - city (str): 城市
                - state (str): 州/省/地区
                - country (str): 国家名（英文）
                - postcode (int | str): 邮政编码（注意：有的国家为字符串）
                - coordinates (dict): { latitude (str), longitude (str) }  # 字符串表示经纬度
                - timezone (dict): { offset (str), description (str) }
            - email (str): 邮箱
            - login (dict): 登录相关演示信息（非安全凭据）
                - uuid (str)
                - username (str)
                - password (str)        # 明文样例，仅演示用
                - salt (str), md5/sha1/sha256 (str)  # 样例摘要
            - dob (dict): 出生信息 { date (str, ISO8601), age (int) }
            - registered (dict): 注册信息 { date (str, ISO8601), age (int) }
            - phone (str), cell (str): 电话/手机（演示）
            - id (dict): 身份标识（演示；不同国家格式不同）{ name (str), value (str|None) }
            - picture (dict): 头像 URL { large/medium/thumbnail (str) }
            - nat (str): 国别代码（ISO 3166-1 alpha-2，如 "US"、"GB"、"RS" 等）
        info 典型字段:
            - seed (str): 随机种子（用于复现实验）
            - results (int): 返回条数
            - page (int): 页码
            - version (str): API 版本（如 "1.4"）

    请求行为与可选参数（本函数未内置参数拼接，以下供上层调用参考）:
        - `?results=10`            : 返回 10 条记录（适合批量生成）。
        - `?gender=male|female`    : 性别过滤。
        - `?nat=US,GB,AU,...`      : 国别过滤，可用多个逗号分隔。
        - `?inc=field1,field2`     : 仅包含指定字段（如 `name,email`），可减少数据量。
        - `?exc=field1,field2`     : 排除指定字段（如 `login,registered`）。
        - `?seed=xxxx`             : 固定种子，保证相同请求返回一致结果（利于测试可重复）。
        - `?noinfo`                : 顶层去掉 `info` 字段。
        示例（如需自定义，可由上层自行构造 URL）:
            https://randomuser.me/api/?results=10&gender=female&nat=US,GB&inc=name,email,picture&noinfo

    稳定性与可靠性:
        - 托管: Cloudflare 全球 CDN，常年在线，可靠性高。
        - 速率: 官方未给出严格配额，**建议合理调用**；高并发/批量场景应加入退避重试（指数退避）与缓存。
        - 可用性: 偶发 5xx/超时属正常网络现象，上层应具备容错与降级策略（如切换 seed/缩小 results）。

    编码与类型注意事项:
        - 姓名/地址可能包含非 ASCII 字符（示例中含有重音/变音符号）；请确保终端/存储使用 UTF-8。
        - `postcode` 可能为数字或字符串（取决于国家）；解析/入库请做好类型兼容。
        - 经度/纬度为字符串格式（如 "59.8685"）；若需地理计算，请自行转换为 float。

    安全与隐私:
        - 返回数据为**合成/演示数据**，不对应真实个人；可安全用于测试、占位、演示。
        - `login.password/md5/sha1/sha256` 为样例字段，不可用于安全校验或生产账户逻辑。

    错误处理策略:
        - 网络异常/超时/非 200 状态码 → 返回 None。
        - JSON 解析异常（极少见） → 返回 None。
        - 上层如需错误细节（trace、状态码、原文），请在本函数外层封装重试与日志记录。

    Returns:
        dict | None:
            - 成功: 返回接口的**完整原始 JSON**（包含 `results` 和 `info`）。
            - 失败: 返回 None。
    """
    try:
        响应 = requests.get("https://randomuser.me/api/", timeout=5)
        if 响应.status_code == 200:
            数据 = 响应.json()
            return 数据
        return None
    except Exception:
        return None
