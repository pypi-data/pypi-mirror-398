# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     po_utils.py
# Description:  po对象处理工具
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Literal, Union, Tuple
from playwright.async_api import Page, Locator

MouseButton = Literal["left", "middle", "right"]


async def on_click_locator(locator: Locator, button: MouseButton = "left") -> bool:
    try:
        await locator.click(button=button)
        return True
    except(Exception,):
        return False


async def on_click_element(page: Page, selector: str, button: MouseButton = "left") -> bool:
    try:
        await page.locator(selector).click(button=button)
        return True
    except(Exception,):
        return False


async def locator_input_element(locator: Locator, text: str) -> bool:
    """
    输入内容，输入前会自动清空原来的内容
    :param locator: Locator对象
    :param text: 输入的内容
    :return:
    """
    try:
        # 填入文字，会清空原内容
        if isinstance(text, str) is False:
            text = str(text)
        await locator.fill(text)
        return True
    except (Exception,):
        return False


async def simulation_input_element(locator: Locator, text: str, delay: int = 100) -> bool:
    """
    模拟逐字符输入（可用于触发 JS 事件）
    :param locator: 元素定位器对象
    :param text: 输入的内容
    :param int delay: 每个字符延迟输入 100ms
    :return:
    """
    try:
        if isinstance(text, str) is False:
            text = str(text)
        await locator.type(text, delay=delay)
        return True
    except (Exception,):
        return False


async def page_screenshot(page: Page, file_name: str = None, is_full_page: bool = False) -> Union[bytes, None]:
    """
    保存截图，默认截图整个可见页面（不是整个滚动区域）
    :param page:
    :param file_name: 文件名，若没传递，这返回bytes
    :param is_full_page: true---> 截图整个网页（包括滚动区域）
    :return:
    """
    if is_full_page is True:
        if file_name is None:
            return await page.screenshot()
        await page.screenshot(path=file_name, full_page=True)
    else:
        await page.screenshot(path=file_name)


async def locator_element_screenshot(locator: Locator, file_name: str = None) -> bytes:
    """
    元素截图
    :param locator: Locator对象
    :param file_name: 文件名，若没传递，这返回bytes
    :return:
    """
    if file_name is None:
        return await locator.screenshot(path=file_name)

    else:
        await locator.screenshot(path=file_name)


async def is_exists_value(element: Locator) -> Tuple[bool, Union[str, None]]:
    """
    判断一个元素是否存在值
    :param element:
    :return:
    """
    value = await element.input_value()
    # value = await element.get_attribute("value")
    if value:
        value = value.strip()
        if len(value) > 0:
            return True, value
        else:
            return False, None
    else:
        return False, None
