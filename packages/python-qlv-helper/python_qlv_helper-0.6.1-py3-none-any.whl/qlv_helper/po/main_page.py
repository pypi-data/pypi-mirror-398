# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     main_page.py
# Description:  首页页面对象
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Tuple, Union
from playwright_helper.libs.base_po import BasePo
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator


class MainPage(BasePo):
    url: str = "/"
    __page: Page

    def __init__(self, page: Page, url: str = "/") -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_confirm_btn_with_system_notice_dialog(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        """
        获取系统通知弹框中的确认按钮，注意这个地方，存在多个叠加的弹框，因此用last()方法，只需定位到最上面的那个弹框就行
        :return:
        """
        selector: str = "//div[@class='CommonAlert'][last()]//a[@class='CommonAlertBtnConfirm']"
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到首页中的【系统提醒-确定】按钮'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_level1_menu_order_checkout(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        selector: str = "//span[contains(normalize-space(), '订单出票')]"
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到首页中的【订单出票】左侧一级导航菜单'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_level2_menu_order_checkout(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        selector: str = "//a[@menuname='国内活动订单']"
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到首页中的【国内活动订单】左侧二级导航菜单'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"
