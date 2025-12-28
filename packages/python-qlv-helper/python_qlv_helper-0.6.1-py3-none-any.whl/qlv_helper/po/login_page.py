# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     login.py
# Description:  登录页
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Tuple, Union
from playwright_helper.libs.base_po import BasePo
from qlv_helper.utils.ocr_helper import get_image_text
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator


class LoginPage(BasePo):
    __page: Page

    def __init__(self, page: Page, url: str = "/Home/Login") -> None:
        super().__init__(page, url)
        self.__page = page

    async def get_login_username_input(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        """
        获取登录页面的用户名输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        :return:
        """
        selector: str = '//input[@id="UserName"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【用户名】输入框'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_login_password_input(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        """
        获取登录页面的密码输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        :return:
        """
        selector: str = '//input[@id="Password"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【密码】输入框'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_login_number_code_input(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        """
        获取登录页面的数字验证码输入框，第一层验证码
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        :return:
        """
        selector: str = '//input[@id="Code"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【数字验证码】输入框'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_login_btn(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        """
        获取登录页面的登录按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        :return:
        """
        selector: str = '//input[@class="login-btn"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【登录】按钮'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    async def get_number_code(self, timeout: float = 5.0) -> Tuple[bool, str]:
        selector: str = '//div[@id="signup_forms"]//img'
        return await get_image_text(page=self.__page, selector=selector, timeout=timeout)

    async def is_exist_login_warn(self, timeout: float = 5.0) -> bool:
        selector: str = '//p[@class="login_warn"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                text: str = await locator.text_content(timeout=timeout * 1000)
                if text.strip() != "":
                    return True
                else:
                    return False
            else:
                return False
        except (PlaywrightTimeoutError, Exception):
            return False

    async def get_wechat_entrance(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        selector: str = '//img[@src="/images/weixin.png"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【微信】快捷登录入口'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"
