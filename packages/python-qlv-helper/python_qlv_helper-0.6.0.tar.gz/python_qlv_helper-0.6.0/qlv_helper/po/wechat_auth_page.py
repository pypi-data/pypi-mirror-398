# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     wechat_auth_page.py
# Description:  微信认证页面对象
# Author:       ASUS
# CreateDate:   2025/11/27
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import os
import asyncio
from typing import Tuple, Union
from playwright_helper.libs.base_po import BasePo
from qlv_helper.utils.file_handle import get_caller_dir
from qlv_helper.utils.windows_utils import gen_allow_btn_image, windows_on_click
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator


class WechatAuthPage(BasePo):
    __page: Page

    def __init__(self, page: Page, url: str = "/connect/qrconnect") -> None:
        super().__init__(page, url)
        self.__page = page

    async def get_wechat_quick_login_btn(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        selector: str = '//*[@id="tpl_for_page"]//button[text()="微信快捷登录"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【微信快捷登录】按钮'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_dialog_allow_btn(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        selector: str = '//div[@id="dialog_allow_btn"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '，没有找到申请登录弹框中的【允许】按钮'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def on_click_allow_btn(self, timeout: int = 5) -> Tuple[bool, str]:
        try:
            image_name = os.path.join(get_caller_dir(), "allow_btn_image.png")
            gen_allow_btn_image(image_name=image_name)
            await asyncio.sleep(delay=timeout)
            windows_on_click(image_name=image_name, windows_title="微信", is_delete=True)
            await asyncio.sleep(delay=timeout)
            if self.is_current_page():
                return False, "【微信快捷登录】登录失败，需要重新登录"
            else:
                return True, "【微信快捷登录】登录成功"
        except Exception as e:
            return False, str(e)
