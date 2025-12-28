"""zfx.playwright 使用说明（面向小白）

概述:
    这是 zfx.playwright 模块的入门说明函数，旨在用最少的门槛带你从 0 到 1
    完成 Playwright 的安装与基本运行环境准备。该函数返回一段可打印的长字符串，
    包含：Playwright 是什么、能做什么、如何安装、如何验证、常见报错与解决方案。

注意:
    - 我们遵循 zfx 的封装约定：本说明避免出现 Playwright 原生调用示例，
      仅聚焦“环境与安装”。真正的 API 调用请看 zfx.playwright 的其他函数。

函数风格:
    - 文档字符串采用 Google 风格。
    - 不包含任何以 ">>>" 开头的交互式示例。

"""
from __future__ import annotations

from typing import Final


def 使用说明() -> str:
    """返回 Playwright 的中文入门说明文本。

    功能说明:
        汇总 Playwright 的基础概念与安装步骤，覆盖 Windows / macOS / Linux / WSL
        的常见环境，并给出“只安装某个浏览器内核”、“离线/受限网络安装”、
        “服务器依赖安装”、“代理与镜像配置”等实用指令，方便一键复制执行。

    Returns:
        str: 可直接打印或写入到文件的长文本，适合发给新同事或初学者。

    内部说明:
        - 文本仅介绍环境准备，不涉及 API 代码示例；
        - 后续请配合 `初始化_普通模式()` / `初始化_禁用图片()` 等函数食用。
    """
    标题: Final[str] = (
        "Playwright 安装与环境准备（zfx.playwright 版 · 小白友好）\n"
        "============================================================\n"
    )

    什么是: Final[str] = (
        "【Playwright 是什么】\n"
        "Playwright 是微软开源的跨浏览器自动化测试与爬取框架。它可以用同一套脚本\n"
        "驱动 Chromium（Chrome/Edge）、Firefox、WebKit（Safari）三大内核，\n        支持图形界面/无头模式、同步/异步 API、强大的选择器与网络拦截能力。\n"
        "zfx.playwright 在其之上做了中文友好封装，统一风格、统一错误处理，\n"
        "让你“只管业务，不操心底层细节”。\n\n"
    )

    能做什么: Final[str] = (
        "【它能做什么】\n"
        "1) 自动化打开网页、填写表单、点击按钮、滚动、截图/录屏；\n"
        "2) 抓取信息：读取元素文本/HTML、等待渲染、批量解析列表；\n"
        "3) 网络层：拦截/修改请求、屏蔽图片/媒体以提速、读取 XHR/fetch 数据；\n"
        "4) 稳定性：自带等待机制与选择器策略，适合构建健壮的采集/测试脚本；\n"
        "5) 跨平台：Windows / macOS / Linux / WSL 一套脚本多端运行。\n\n"
    )

    安装总览: Final[str] = (
        "【安装总览：两步走（CMD 或 PowerShell下执行命令）】\n"
        "第 1 步：安装 Python 侧依赖（Playwright 的 Python 封装）\n"
        "    pip install playwright\n\n"
        "第 2 步：安装浏览器运行环境（下载 Chromium/Firefox/WebKit 内核）\n"
        "    # 安装全部内核（推荐）\n"
        "    playwright install\n\n"
        "    # 只装某一个（更省空间/带宽），任选其一（不推荐）：\n"
        "    playwright install chromium\n"
        "    playwright install firefox\n"
        "    playwright install webkit\n\n"
        "验证：\n"
        "    playwright --version\n"
        "    # 若能显示版本且 `playwright install --list` 能看到已安装的浏览器，\n"
        "    # 就说明环境 OK。\n\n"
    )

    结束语: Final[str] = (
        "【接下来干嘛】\n"
        "环境就绪后，建议首先尝试 zfx.playwright 的初始化函数：\n"
        "- 初始化_普通模式()：启动浏览器并返回“引擎/浏览器/上下文/页面”四件套；\n"
        "- 初始化_禁用图片()：默认屏蔽图片/字体/媒体等重资源，速度更快。\n"
        "然后再看 `页面_访问网页()`、`页面_获取元素文本()` 等函数，循序渐进即可。\n"
    )

    return 标题 + 什么是 + 能做什么 + 安装总览 + 结束语