# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     browser_utils.py
# Description:  浏览器工具模块
# Author:       ASUS
# CreateDate:   2025/11/27
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
from typing import Optional
from playwright.async_api import BrowserContext, Page


async def switch_for_table_window(browser: BrowserContext, url_keyword: str, wait_time: int = 10) -> Optional[Page]:
    # 最多等待 wait_time 秒
    for _ in range(wait_time):
        await asyncio.sleep(1)
        for page in browser.pages:
            if url_keyword.lower() in page.url.lower():
                await page.bring_to_front()
                return page
    return None
