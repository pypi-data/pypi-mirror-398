# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     activity_order_table_page.py
# Description:  活动订单表页面的HTTP响应处理模块
# Author:       zhouhanlin
# CreateDate:   2025/11/30
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re
import aiohttp
from html import unescape
from copy import deepcopy
from urllib.parse import unquote
from collections import OrderedDict
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup, ResultSet, Tag
from http_helper.client.async_proxy import HttpClientFactory
from qlv_helper.utils.type_utils import get_key_by_index, get_value_by_index, safe_convert_advanced

kwargs = {
    "orderbykey": None,
    "orderbydescOrAsc": None,
    "oldorderbykey": "ID",
    "isorderby": False,
    "ID": 0,
    "IOrderNO": None,
    "hid": 1,
    "JumpPageFromPage": 2,
    "PageCountFormPage": 100
}


async def get_domestic_activity_order_page_html(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None, current_page: int = 1,
        pages: int = 1, order_http_client: HttpClientFactory = None, is_end: bool = True
) -> Dict[str, Any]:
    if not order_http_client:
        order_http_client = HttpClientFactory(
            protocol=protocol if protocol == "http" else "https",
            domain=domain,
            timeout=timeout,
            retry=retry,
            enable_log=enable_log,
            cookie_jar=cookie_jar,
            playwright_state=playwright_state
        )
    url = "/OrderList/GuoNei_ActivityOrders"
    if current_page == 1:
        return await order_http_client.request(method="get", url=url, is_end=is_end)
    else:
        json_data = deepcopy(kwargs)
        json_data["JumpPageFromPage"] = current_page
        json_data["PageCountFormPage"] = pages
        return await order_http_client.request(method="post", url=url, is_end=is_end, json_data=json_data)

async def get_domestic_ticket_outed_page_html(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None, current_page: int = 1,
        pages: int = 1, order_http_client: HttpClientFactory = None, is_end: bool = True
) -> Dict[str, Any]:
    if not order_http_client:
        order_http_client = HttpClientFactory(
            protocol=protocol if protocol == "http" else "https",
            domain=domain,
            timeout=timeout,
            retry=retry,
            enable_log=enable_log,
            cookie_jar=cookie_jar,
            playwright_state=playwright_state
        )
    url = "/OrderList/GuoNei_TicketOuted"
    if current_page == 1:
        return await order_http_client.request(method="get", url=url, is_end=is_end)
    else:
        json_data = deepcopy(kwargs)
        json_data["JumpPageFromPage"] = current_page
        json_data["PageCountFormPage"] = pages
        return await order_http_client.request(method="post", url=url, is_end=is_end, json_data=json_data)

async def get_domestic_unticketed_order_page_html(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None, current_page: int = 1,
        pages: int = 1, order_http_client: HttpClientFactory = None, is_end: bool = True
) -> Dict[str, Any]:
    if not order_http_client:
        order_http_client = HttpClientFactory(
            protocol=protocol if protocol == "http" else "https",
            domain=domain,
            timeout=timeout,
            retry=retry,
            enable_log=enable_log,
            cookie_jar=cookie_jar,
            playwright_state=playwright_state
        )
    url = "/OrderList/GuoNei_TicketOutUndo"
    if current_page == 1:
        return await order_http_client.request(method="get", url=url, is_end=is_end)
    else:
        json_data = deepcopy(kwargs)
        json_data["JumpPageFromPage"] = current_page
        json_data["PageCountFormPage"] = pages
        return await order_http_client.request(method="post", url=url, is_end=is_end, json_data=json_data)


def processing_static_headers() -> OrderedDict[str, str]:
    return OrderedDict([
        ("source_name", "来源"),  # 0
        ("id", "订单号"),  # 1
        ("raw_order_no", "平台订单号"),  # 2
        ("adult_pnr", "成人PNR"),  # 3
        ("payment_time", "支付时间"),  # 4
        ("sec_from_pay", "支付秒数"),  # 5
        ("last_time_ticket", "出票时限"),  # 6
        ("remaining_time", "剩余秒数"),  # 7
        ("dat_dep", "起飞时间"),  # 8
        ("policy", "政策"),  # 9
        ("total_people", "总人数"),  # 10
        ("receipted", "总价"),  # 11
        ("stat_opration", "订单操作"),  # 12
        ("more_seats", "余座"),  # 13
        ("operation", "操作"),  # 14
    ])


def completed_static_headers() -> OrderedDict[str, str]:
    return OrderedDict([
        ("source_name", "来源"),  # 0
        ("id", "订单号"),  # 1
        ("raw_order_no", "平台订单号"),  # 2
        ("adult_pnr", "成人PNR"),  # 3
        ("payment_time", "支付时间"),  # 4
        ("checkout_ticket", "下单时间"),  # 5
        ("dat_dep", "起飞时间"),  # 6
        ("policy_name", "政策"),  # 7
        ("total_people", "总人数"),  # 8
        ("receipted", "总价"),  # 9
        ("stat_opration", "订单操作"),  # 10
        ("operation", "操作"),  # 11
    ])


def extend_headers() -> OrderedDict[str, str]:
    return OrderedDict([
        ("detail_link", "详情链接"),  # 0
        ("child_pnr", "儿童PNR"),  # 1
        ("code_dep", "起飞机场"),  # 2
        ("code_arr", "抵达机场"),  # 3
        ("flight_no", "航班号"),  # 4
        ("cabin", "舱位"),  # 5
        ("total_adult", "成人数量"),  # 6
        ("total_child", "儿童数量"),  # 7
    ])


def parse_order_table_headers(html: BeautifulSoup) -> OrderedDict[str, str]:
    """
    解析订单表头
    """
    headers = OrderedDict()
    header_rows = html.find_all('tr')

    # 处理表头，注意有些th有colspan属性
    for th in header_rows[0].find_all('th'):
        header_text = th.get_text(strip=True)

        # 检查th内部是否有多个span
        spans = th.find_all('span')
        if len(spans) > 1:
            # 如果有多个span，每个span都作为一个独立的表头
            for span in spans:
                span_text = span.get_text(strip=True)
                if span_text:
                    if span_text.find("(") != -1:
                        span_text = span_text.replace("(", "/")
                        span_text = span_text.replace(")", "/")
                        for x in span_text.split("/"):
                            headers[x] = x
                    else:
                        headers[span_text] = span_text
        elif header_text.find("|") != -1:
            header_text_slice = header_text.split("|")
            header_text_slice = [x.strip() for x in header_text_slice]
            for x in header_text_slice:
                headers[x] = x
        else:
            headers[header_text] = header_text

    return headers


def clean_cell_content(cell):
    """
    清理单元格内容
    """
    # 提取文本
    text = cell.get_text(' ', strip=True)
    # 解码HTML实体
    text = unescape(text)
    # 清理多余空格
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def extract_special_attributes(cells, order_data: Dict[str, Any], header: OrderedDict[str, str]):
    """
    提取单元格的特殊属性
    """
    sec_from_pay_key = get_key_by_index(header, 5)
    remaining_time_key = get_key_by_index(header, 7)
    stat_opration_key = get_key_by_index(header, 12)
    for i, cell in enumerate(cells):
        # 提取支付秒数
        if 'secFrmPay' in cell.get('class', []):
            tag_value = cell.get('tag', '')
            if tag_value:
                order_data[sec_from_pay_key] = int(tag_value)
            else:
                order_data[sec_from_pay_key] = None

        # 提取剩余时间
        if 'remainingtime' in cell.get('class', []):
            remaining_time = cell.get('remainingtime', '')
            state = cell.get('state', '')
            if remaining_time:
                order_data[remaining_time_key] = int(remaining_time)
            else:
                order_data[remaining_time_key] = None
            if state:
                order_data[stat_opration_key] = state
            else:
                order_data[stat_opration_key] = None


def parse_order_row(cells: ResultSet[Tag], headers: OrderedDict, extend_headers: OrderedDict, row_index: int):
    """
    解析单行订单数据
    """
    order_data = dict()

    for i, cell in enumerate(cells):
        try:
            if i >= len(headers):
                break

            header_value = get_value_by_index(ordered_dict=headers, index=i)
            header_key = get_key_by_index(ordered_dict=headers, index=i)
            cell_text = clean_cell_content(cell)

            # 特殊字段处理
            if header_key == "id":
                if "紧急" in cell_text:
                    cell_text = cell_text.split(" ")[0]
                order_data[header_key] = int(cell_text)

                # 提取订单号链接
                detail_link_key = get_key_by_index(ordered_dict=extend_headers, index=0)
                link = cell.find('a')
                if link and 'OrderNavigation' in link.get('href', ''):
                    order_data[detail_link_key] = unquote(link.get('href', ""))
                else:
                    order_data[detail_link_key] = None
            elif header_value == '操作':
                # 解析操作按钮信息
                cell_text_slice = cell_text.split(" ")
                order_data[header_key] = cell_text_slice[0]
            elif 'PNR' in header_value:
                # 清理PNR信息
                pnr_text = cell_text.replace('&nbsp;|&nbsp;', ' | ')
                adult_pnr_key = get_key_by_index(ordered_dict=headers, index=3)
                child_pnr_key = get_key_by_index(ordered_dict=extend_headers, index=1)
                pnr_text_slice = pnr_text.split("|")
                order_data[adult_pnr_key] = pnr_text_slice[0].strip()
                order_data[child_pnr_key] = pnr_text_slice[-1].strip() if pnr_text_slice[-1] else None
            elif header_value in "起飞时间":
                cell_text_slice = cell_text.split(" ")
                if len(cell_text_slice) == 5:
                    code_dep_key = get_key_by_index(ordered_dict=extend_headers, index=2)
                    code_arr_key = get_key_by_index(ordered_dict=extend_headers, index=3)
                    flight_no_key = get_key_by_index(ordered_dict=extend_headers, index=4)
                    cabin_key = get_key_by_index(ordered_dict=extend_headers, index=5)
                    order_data[header_key] = f"{cell_text_slice[0]} {cell_text_slice[1]}"
                    itinerary_slice = cell_text_slice[2].split("-")
                    order_data[code_dep_key] = itinerary_slice[0]
                    order_data[code_arr_key] = itinerary_slice[-1]
                    order_data[flight_no_key] = cell_text_slice[3]
                    order_data[cabin_key] = cell_text_slice[4]
            elif header_value in "总人数":
                cell_text = cell_text.replace("【", "/")
                cell_text = cell_text.replace("】", "/")
                cell_text_slice = cell_text.split("/")
                order_data[header_key] = safe_convert_advanced(cell_text_slice[0])
                total_adult_key = get_key_by_index(ordered_dict=extend_headers, index=6)
                total_child_key = get_key_by_index(ordered_dict=extend_headers, index=7)
                order_data[total_adult_key] = safe_convert_advanced(cell_text_slice[1])
                order_data[total_child_key] = safe_convert_advanced(cell_text_slice[2])
            elif header_key == "receipted":
                order_data[header_key] = safe_convert_advanced(cell_text)
            else:
                order_data[header_key] = cell_text

            # 提取特殊属性
            extract_special_attributes(cells=cells, order_data=order_data, header=headers)
        except Exception as e:
            print(f"解析第{row_index + 1}行时出错: {e}")

    return order_data


def parse_order_table(html: str, table_state: str = "proccessing") -> List[Optional[Dict[str, Any]]]:
    """
    解析订单表格数据
    """
    soup = BeautifulSoup(html, 'html.parser')
    orders = list()

    # 找到目标表格
    table = soup.find('table', {'class': 'table table_hover table_border table_center'})
    if not table:
        return orders

    # 解析表头（处理复杂的th结构）
    if table_state == "proccessing":
        headers = processing_static_headers()
    elif table_state == "completed":
        headers = completed_static_headers()
    else:
        headers = parse_order_table_headers(html=table)
    extend = extend_headers()

    # 解析数据行（从第二个tr开始）
    data_rows = table.find_all('tr')[1:]  # 跳过表头行

    for i, row in enumerate(data_rows):
        # 跳过隐藏的input行
        if row.find('input', {'name': 'hidOrderID'}):
            continue

        cells = row.find_all(['td', 'th'])

        order_data = parse_order_row(cells, headers=headers, extend_headers=extend, row_index=i)
        if order_data and order_data.get("id") is not None:
            orders.append(order_data)

    return orders
