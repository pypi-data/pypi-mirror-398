# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     main_page.py
# Description:  首页的HTTP响应处理模块
# Author:       ASUS
# CreateDate:   2025/11/29
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from http_helper.client.async_proxy import HttpClientFactory


async def get_main_page_html(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    order_http_client = HttpClientFactory(
        protocol=protocol if protocol == "http" else "https",
        domain=domain,
        timeout=timeout,
        retry=retry,
        enable_log=enable_log,
        cookie_jar=cookie_jar,
        playwright_state=playwright_state
    )
    return await order_http_client.request(method="get", url="/", is_end=True)


def parser_head_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # 提取 title 文本
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text().strip()
    else:
        return ""
