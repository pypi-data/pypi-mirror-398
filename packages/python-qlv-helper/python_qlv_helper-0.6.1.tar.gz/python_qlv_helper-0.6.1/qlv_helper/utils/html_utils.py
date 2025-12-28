# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     html_utils.py
# Description:  html处理工具模块
# Author:       zhouhanlin
# CreateDate:   2025/12/01
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, Any


def parse_pagination_info(html: str) -> Dict[str, Any]:
    """
    解析分页信息
    """
    soup = BeautifulSoup(html, 'html.parser')

    pagination_info = {
        "current_page": 1,
        "pages": 1,
        "is_next_page": False,
        "is_pre_page": False,
        "total": 0,
        "page_size": 20
    }

    # 找到分页的div
    pagination_div = soup.find('div', {'class': 'redirect'})
    if not pagination_div:
        return pagination_info

    # 解析两个label
    labels = pagination_div.find_all('label')

    if len(labels) >= 2:
        # 当前页码
        pagination_info["current_page"] = int(labels[0].get_text(strip=True))
        # 总页数
        pagination_info["pages"] = int(labels[1].get_text(strip=True))

    # 解析显示记录信息
    span_text = pagination_div.find('span').get_text(strip=True) if pagination_div.find('span') else ''
    # 提取数字
    numbers = re.findall(r'\d+', span_text)
    if len(numbers) >= 3:
        pagination_info["page_size"] = int(numbers[1])
        pagination_info["total"] = int(numbers[2])

    if pagination_info["current_page"] == 1:
        pagination_info["is_pre_page"] = False
    if pagination_info["pages"] > 1 and pagination_info["current_page"] < pagination_info["pages"]:
        pagination_info["is_next_page"] = True

    return pagination_info
