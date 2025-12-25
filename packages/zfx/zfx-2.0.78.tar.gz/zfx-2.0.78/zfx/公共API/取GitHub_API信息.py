import requests


def 取GitHub_API信息() -> dict | None:
    """
    获取 GitHub 公共 API 根端点信息。

    功能说明:
        访问 GitHub 官方公共接口:
            https://api.github.com
        该接口为 GitHub REST API 的根端点，无需认证即可访问。
        返回内容为 JSON 格式，包含以下主要字段:
            - current_user_url: 当前用户接口地址。
            - current_user_authorizations_html_url: 授权页面地址。
            - authorizations_url: 授权接口。
            - code_search_url / commit_search_url: 搜索相关接口。
            - repository_url / issues_url / gists_url: 各资源接口模板。
            - rate_limit_url: 当前速率限制查询地址。
            - emojis_url / events_url: 其他公共资源。
        可用于检测 GitHub 网络连通性、API 状态或版本信息。
        若请求失败或返回异常，函数返回 None。

    Returns:
        dict | None:
            - 成功时返回 GitHub API 根端点的 JSON 信息。
            - 请求失败或异常时返回 None。
    """
    url = "https://api.github.com"
    try:
        响应对象 = requests.get(url, timeout=5)
        if 响应对象.status_code == 200:
            return 响应对象.json()
        return None
    except Exception:
        return None
