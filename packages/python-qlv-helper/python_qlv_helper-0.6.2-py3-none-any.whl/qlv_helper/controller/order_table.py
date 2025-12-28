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
from copy import deepcopy
from logging import Logger
from aiohttp import CookieJar
from datetime import datetime, timedelta
from playwright.async_api import Page, Locator
import qlv_helper.config.url_const as url_const
from http_helper.client.async_proxy import HttpClientFactory
from qlv_helper.utils.html_utils import parse_pagination_info
from qlv_helper.utils.type_utils import safe_convert_advanced
from typing import Optional, Dict, Any, Callable, List, cast, Tuple
from qlv_helper.po.domestic_activity_order_page import DomesticActivityOrderPage
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
        fetch_page_fn: Callable[..., Any],  # 拿到第一页/分页 HTML 的函数
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
        except (Exception,):
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


async def open_domestic_activity_order_page(
        *, page: Page, logger: Logger, qlv_protocol: str, qlv_domain: str, timeout: float = 20.0
) -> DomesticActivityOrderPage:
    url_prefix = f"{qlv_protocol}://{qlv_domain}"
    domestic_activity_order_url = url_prefix + url_const.domestic_activity_order_url
    await page.goto(domestic_activity_order_url)

    domestic_activity_order_po = DomesticActivityOrderPage(page=page, url=domestic_activity_order_url)
    await domestic_activity_order_po.url_wait_for(url=domestic_activity_order_url, timeout=timeout)
    logger.info(f"即将进入国内活动订单页面，页面URL<{domestic_activity_order_url}>")
    return domestic_activity_order_po


async def pop_will_expire_domestic_activity_order(
        *, page: Page, logger: Logger, qlv_protocol: str, qlv_domain: str, last_minute_threshold: int,
        timeout: float = 20.0, **kwargs: Any
) -> Tuple[List[Dict[str, Any]], bool]:
    # 1. 打开国内活动订单页面
    domestic_activity_order_po = await open_domestic_activity_order_page(
        page=page, logger=logger, qlv_protocol=qlv_protocol, qlv_domain=qlv_domain, timeout=timeout
    )

    # TODO 暂时不考虑分页的情况
    # 2. 获取table所有tr的Locator对象
    trs_locator = await domestic_activity_order_po.get_flight_table_trs_locator(timeout=timeout)
    trs_locator = await trs_locator.all()
    table_data = list()
    feilds = {
        "to_from": "", "urgant_state": "", "order_id": 0, "pre_order_id": "", "aduit_pnr": "", "child_pnr": "",
        "payment_time": "", "last_time_ticket": "", "dat_dep": "", "code_dep": "", "code_arr": "", "flight_no": "",
        "cabin": "", "policy": "", "total_people": 0, "total_adult": 0, "total_child": 0, "receipted": 0.00,
        "stat_opration": "", "more_seats": "", "operation_info": "", "substitute_btn_locator": ""
    }
    pre_pop_orders = list()
    is_pop = False
    for tr_locator in trs_locator[1:]:
        row_locator = await domestic_activity_order_po.get_flight_table_trs_td(locator=tr_locator, timeout=timeout)
        tds_locators = await row_locator.all()
        sub_feilds = list()
        copy_feilds = deepcopy(feilds)
        for index, td_locator in enumerate(tds_locators):
            try:
                text = (await td_locator.inner_text()).strip()
                if index == 0:
                    copy_feilds["to_from"] = text
                    sub_feilds.append("to_from")
                elif index == 1:
                    order_id = await domestic_activity_order_po.get_flight_table_td_order_id(
                        locator=td_locator, timeout=timeout
                    )
                    urgant_state = await domestic_activity_order_po.get_flight_table_td_urgant(
                        locator=td_locator, timeout=timeout
                    )
                    copy_feilds["order_id"] = safe_convert_advanced(value=order_id)
                    copy_feilds["urgant_state"] = urgant_state
                    sub_feilds.extend(["order_id", "urgant_state"])
                elif index == 2:
                    copy_feilds["pre_order_id"] = text
                    sub_feilds.append("pre_order_id")
                elif index == 3:
                    text = text.replace("\xa0", "")
                    text_slice = text.split("|")
                    copy_feilds["aduit_pnr"] = text_slice[0].strip()
                    copy_feilds["child_pnr"] = text_slice[1].strip()
                    sub_feilds.extend(["aduit_pnr", "child_pnr"])
                elif index == 4:
                    copy_feilds["payment_time"] = text
                    sub_feilds.append("payment_time")
                elif index == 5:
                    continue
                elif index == 6:
                    copy_feilds["last_time_ticket"] = text
                    sub_feilds.append("last_time_ticket")
                elif index == 7:
                    continue
                elif index == 8:
                    text = text.replace("\xa0", "|")
                    text_slice = [i for i in text.split("|") if i.strip()]
                    ctrip = text_slice[1].split("-")
                    copy_feilds["dat_dep"] = text_slice[0].strip()
                    copy_feilds["code_dep"] = ctrip[0].strip()
                    copy_feilds["code_arr"] = ctrip[1].strip()
                    copy_feilds["flight_no"] = text_slice[2].strip()
                    copy_feilds["cabin"] = text_slice[3].strip()
                    sub_feilds.extend(["dat_dep", "code_dep", "code_arr", "flight_no", "cabin"])
                elif index == 9:
                    text = text.replace("\xa0", "")
                    text = text.replace(">", "")
                    text = text.replace("<", "")
                    text = text.replace("&", "")
                    text = text.replace("<br>", "\n")
                    copy_feilds["policy"] = text
                    sub_feilds.append("policy")
                elif index == 10:
                    text = text.replace("【 ", "|")
                    text = text.replace("/", "|")
                    text = text.replace("】", "")
                    text_slice = text.split("|")
                    copy_feilds["total_people"] = safe_convert_advanced(value=text_slice[0].strip())
                    copy_feilds["total_adult"] = safe_convert_advanced(value=text_slice[1].strip())
                    copy_feilds["total_child"] = safe_convert_advanced(value=text_slice[2].strip())
                    sub_feilds.extend(["total_people", "total_adult", "total_child"])
                elif index == 11:
                    copy_feilds["receipted"] = safe_convert_advanced(value=text)
                    sub_feilds.append("receipted")
                elif index == 12:
                    copy_feilds["stat_opration"] = text
                    sub_feilds.append("stat_opration")
                elif index == 13:
                    copy_feilds["more_seats"] = safe_convert_advanced(value=text)
                    sub_feilds.append("more_seats")
                elif index == 14:
                    text_slice = text.split(" ")
                    operation_info = dict(
                        lock_btn_locator=cast(Locator, None), pop_btn_locator=cast(Locator, None), locked=""
                    )
                    if "锁定" in text_slice[0]:
                        lock_btn_locator = await domestic_activity_order_po.get_flight_table_td_operation_lock_btn(
                            locator=td_locator, timeout=timeout
                        )
                        operation_info["lock_btn_locator"] = lock_btn_locator
                    else:
                        operation_info["locked"] = text_slice[0].strip()
                    if "踢出" in text:
                        pop_btn_locator = await domestic_activity_order_po.get_flight_table_td_operation_pop_btn(
                            locator=td_locator, timeout=timeout
                        )
                        operation_info["pop_btn_locator"] = pop_btn_locator
                    copy_feilds["operation_info"] = operation_info
                    sub_feilds.append("operation_info")
                elif index == 15:
                    copy_feilds[
                        "substitute_btn_locator"
                    ] = await domestic_activity_order_po.get_flight_table_td_operation_substitute_btn(
                        locator=td_locator, timeout=timeout)
                    sub_feilds.append("substitute_btn_locator")
            except (Exception,) as e:
                logger.error(f"第<{index + 1}>列数据处理异常，原因：{e}")
        if len(sub_feilds) == 22:
            table_data.append(copy_feilds)
            if datetime.strptime(
                    copy_feilds.get("last_time_ticket"), "%Y-%m-%d %H:%M:%S"
            ) < datetime.now() + timedelta(minutes=last_minute_threshold):
                pre_pop_orders.append(copy_feilds)
    for pre_pop_order in pre_pop_orders:
        order_id = pre_pop_order.get("order_id")
        operation_info = pre_pop_order.get("operation_info")
        pop_btn_locator = operation_info.get("pop_btn_locator")
        last_time_ticket = pre_pop_order.get("last_time_ticket")
        if pop_btn_locator and isinstance(pop_btn_locator, Locator):
            minute = (datetime.strptime(last_time_ticket, "%Y-%m-%d %H:%M:%S") - datetime.now()).total_seconds() / 60
            await pop_btn_locator.click()
            if is_pop is False:
                is_pop = True
            logger.info(
                f"订单<{order_id}>，距离最晚出票时限: {last_time_ticket}，仅剩<{minute}>分钟，已将工单剔出活动订单"
            )
    return table_data, is_pop
