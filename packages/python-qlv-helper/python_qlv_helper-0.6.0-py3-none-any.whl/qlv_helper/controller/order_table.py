# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     order_table.py
# Description:  订单列表页面控制器
# Author:       ASUS
# CreateDate:   2025/12/01
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
from aiohttp import CookieJar
from typing import Optional, Dict, Any, Callable, List
from http_helper.client.async_proxy import HttpClientFactory
from qlv_helper.utils.html_utils import parse_pagination_info
from qlv_helper.http.order_table_page import get_domestic_activity_order_page_html, get_domestic_ticket_outed_page_html, \
    parse_order_table, get_domestic_unticketed_order_page_html


async def _get_paginated_order_table(
        *,
        domain: str,
        protocol: str,
        retry: int,
        timeout: int,
        enable_log: bool,
        cookie_jar: Optional[CookieJar],
        playwright_state: Dict[str, Any],
        table_state: str,
        fetch_page_fn: Callable[..., Any],   # 拿到第一页/分页 HTML 的函数
) -> Dict[str, Any]:
    """通用分页表格抓取（支持并发）"""

    order_http_client = HttpClientFactory(
        protocol=protocol if protocol == "http" else "https",
        domain=domain,
        timeout=timeout,
        retry=retry,
        enable_log=enable_log,
        cookie_jar=cookie_jar,
        playwright_state=playwright_state
    )

    # --- 1. 先拿第一页(串行) ---
    response = await fetch_page_fn(
        domain=domain, protocol=protocol, retry=retry, timeout=timeout,
        enable_log=enable_log, cookie_jar=cookie_jar, playwright_state=playwright_state,
        order_http_client=order_http_client, is_end=True
    )
    if response.get("code") != 200:
        return response

    html = response["data"]
    table_data: List[Dict[str, Any]] = parse_order_table(html=html, table_state=table_state)

    pagination_info = parse_pagination_info(html)
    pages = pagination_info.get("pages", 1)

    # --- 2. 如果只有 1 页，直接返回 ---
    if pages <= 1:
        pagination_info.update({
            "data": table_data,
            "is_next_page": False,
            "page_size": len(table_data),
            "pages": 1
        })
        response["data"] = pagination_info
        return response

    # --- 3. 多页：并发抓取第 2~pages 页 ---
    async def fetch_page(client: HttpClientFactory, page: int) -> List[Optional[Dict[str, Any]]]:
        """单页抓取任务，用于并发调度"""
        try:
            resp = await fetch_page_fn(
                domain=domain, protocol=protocol, retry=retry, timeout=timeout,
                enable_log=enable_log, cookie_jar=cookie_jar, playwright_state=playwright_state,
                order_http_client=client, current_page=page, pages=pages, is_end=(page == pages)
            )
            if resp.get("code") == 200:
                return parse_order_table(html=resp["data"], table_state=table_state)
        except (Exception, ):
            return list()  # 抓取失败则返回空，不影响整体
        return list()

    # 🔥 并发：一口气抓全部分页
    order_http_client = HttpClientFactory(
        protocol=protocol if protocol == "http" else "https",
        domain=domain,
        timeout=timeout,
        retry=retry,
        enable_log=enable_log,
        cookie_jar=cookie_jar,
        playwright_state=playwright_state
    )
    tasks = [fetch_page(client=order_http_client, page=page) for page in range(2, pages + 1)]
    results = await asyncio.gather(*tasks)

    # 合并表格数据
    for r in results:
        if r:
            table_data.extend(r)

    # --- 4. 构造最终返回数据 ---
    pagination_info.update({
        "data": table_data,
        "is_next_page": False,
        "page_size": len(table_data),
        "pages": 1
    })
    response["data"] = pagination_info
    return response

async def get_domestic_activity_order_table(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    return await _get_paginated_order_table(
        domain=domain,
        protocol=protocol,
        retry=retry,
        timeout=timeout,
        enable_log=enable_log,
        cookie_jar=cookie_jar,
        playwright_state=playwright_state,
        table_state="proccessing",
        fetch_page_fn=get_domestic_activity_order_page_html
    )


async def get_domestic_ticket_outed_table(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    return await _get_paginated_order_table(
        domain=domain,
        protocol=protocol,
        retry=retry,
        timeout=timeout,
        enable_log=enable_log,
        cookie_jar=cookie_jar,
        playwright_state=playwright_state,
        table_state="completed",
        fetch_page_fn=get_domestic_ticket_outed_page_html
    )

async def get_domestic_unticketed_order_table(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    return await _get_paginated_order_table(
        domain=domain,
        protocol=protocol,
        retry=retry,
        timeout=timeout,
        enable_log=enable_log,
        cookie_jar=cookie_jar,
        playwright_state=playwright_state,
        table_state="proccessing",
        fetch_page_fn=get_domestic_unticketed_order_page_html
    )