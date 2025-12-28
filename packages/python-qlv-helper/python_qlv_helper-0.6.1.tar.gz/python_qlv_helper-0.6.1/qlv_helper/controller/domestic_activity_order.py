# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     domestic_activity_order.py
# Description:  国内活动订单页面控制器
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from playwright.async_api import Page
from typing import Tuple, List, Any, Dict
from qlv_helper.po.domestic_activity_order_page import DomesticActivityOrderPage


async def get_domestic_activity_order(page: Page, timeout: float = 5.0) -> Tuple[bool, List[Dict[str, Any]]]:
    order_po = DomesticActivityOrderPage(page=page)
    is_success, username_input = await order_po.get_flight_table(timeout=timeout)
    if is_success is False:
        return is_success, [dict(error_message=username_input)]
    order_data = await order_po.parse_table_with_pagination(refresh_wait_time=timeout * 2)

    return True, order_data
