def 页面_拦截资源(页面, 资源类型列表=None):
    """
    功能：
        拦截页面中某些“资源类型”的网络请求（如图片、字体、样式、媒体等），
        从而达到屏蔽不需要的内容或提升网页加载速度的效果。

    参数：
        - 页面：我们初始化后得到的“页面对象”。
        - 资源类型列表：要拦截的资源类型，可以是列表或元组。
            常见可选值：
              "document"   → 网页文档
              "stylesheet" → 样式表（CSS）
              "image"      → 图片
              "media"      → 音视频
              "font"       → 字体
              "script"     → 脚本（JS）
              "xhr"        → 异步请求（XHR）
              "fetch"      → 异步请求（fetch）
              "websocket"  → WebSocket 连接
              "other"      → 其他未知类型
            默认值：["image"]，表示只屏蔽图片。

    返回：
        - True：拦截规则设置成功
        - False：拦截规则设置失败（同时打印错误信息）

    使用要点：
        1) 需要在“打开网址之前”调用本函数，否则已经发出的请求无法拦截。
        2) 可以多次调用，每次增加不同的拦截规则；后设置的规则优先级更高。
        3) 规则只对当前这个页面有效，如果新建了标签页，需要重新设置。

    示例：
        结果 = 初始化_普通模式()
        if 结果:
            页 = 结果["页面"]
            页面_拦截资源(页, ["image", "font"])   # 屏蔽图片和字体
            页面_访问网页(页, "https://example.com")  # 访问网页
    """
    try:
        if not 资源类型列表:
            资源类型列表 = ["image"]

        def _handle(route, request):
            if request.resource_type in 资源类型列表:
                route.abort()
            else:
                route.continue_()

        页面.route("**/*", _handle)
        return True
    except Exception as e:
        print("拦截资源失败：", e)
        return False
