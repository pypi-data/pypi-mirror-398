# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     main_page.py
# Description:  首页控制器
# Author:       ASUS
# CreateDate:   2025/11/29
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import aiohttp
from typing import Dict, Any, Optional
from qlv_helper.http.main_page import get_main_page_html, parser_head_title


async def get_main_info_with_http(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    response = await get_main_page_html(
        domain=domain, protocol=protocol, retry=retry, timeout=timeout, enable_log=enable_log,
        cookie_jar=cookie_jar, playwright_state=playwright_state
    )
    if response.get("code") != 200:
        return response

    html = response.get("data")
    response["message"] = parser_head_title(html=html)
    return response