# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     user_login.py
# Description:  用户登录页面控制器
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
from typing import Tuple
from qlv_helper.po.login_page import LoginPage
from playwright.async_api import BrowserContext
from qlv_helper.po.wechat_auth_page import WechatAuthPage
from qlv_helper.utils.browser_utils import switch_for_table_window
from qlv_helper.utils.po_utils import on_click_locator, locator_input_element


async def _username_login(login_po: LoginPage, username: str, password: str, timeout: float = 5.0) -> Tuple[bool, str]:
    # 1. 输入用户名
    is_success, username_input = await login_po.get_login_username_input(timeout=timeout)
    if is_success is False:
        return is_success, username_input
    await locator_input_element(locator=username_input, text=username.strip())

    # 2. 输入密码
    is_success, password_input = await login_po.get_login_password_input(timeout=timeout)
    if is_success is False:
        return is_success, username_input
    await locator_input_element(locator=password_input, text=password.strip())

    # 3. 获取一层验证码
    is_success, code_str = await login_po.get_number_code(timeout=timeout)
    if is_success is False:
        return is_success, code_str

    # 4. 输入一层验证码
    is_success, code_input = await login_po.get_login_number_code_input(timeout=timeout)
    if is_success is False:
        return is_success, code_input
    await locator_input_element(locator=code_input, text=code_str.lower())

    # 5. 点击登录
    is_success, login_btn = await login_po.get_login_btn(timeout=timeout)
    if is_success is False:
        return is_success, login_btn
    await on_click_locator(locator=login_btn)


async def _wechat_login(browser: BrowserContext, login_po: LoginPage, timeout: float = 5.0) -> Tuple[bool, str]:
    # 1. 点击微信登录快捷入口
    is_success, wechat_entrance = await login_po.get_wechat_entrance(timeout=timeout)
    if is_success is False:
        return is_success, wechat_entrance
    await on_click_locator(locator=wechat_entrance)

    page_new = await switch_for_table_window(browser=browser, url_keyword="open.weixin.qq.com", wait_time=int(timeout))
    wachat_po = WechatAuthPage(page=page_new)

    # 2. 点击【微信快捷登录】按钮
    is_success, wechat_quick_login_btn = await wachat_po.get_wechat_quick_login_btn(timeout=timeout)
    if is_success is False:
        return is_success, wechat_quick_login_btn
    await on_click_locator(locator=wechat_quick_login_btn)

    # 3. 点击微信弹框的中【允许】按钮
    return await wachat_po.on_click_allow_btn(timeout=int(timeout) * 3)


async def username_login(
        login_po: LoginPage, username: str, password: str, timeout: float = 5.0, retry: int = 3
) -> Tuple[bool, str]:
    # 1. 第一次全流程的登录
    await _username_login(login_po=login_po, username=username, password=password, timeout=timeout)
    for _ in range(retry):
        # 2. 判断是否为当前页
        if login_po.is_current_page() is False:
            return True, f"账号:{username} 登录成功"

        # 3. 判断是否存在登录警告，存在的话，继续输入验证码，再次登录
        is_warn: bool = await login_po.is_exist_login_warn(timeout=timeout)
        if is_warn is True:
            # 4. 获取一层验证码
            is_success, code_str = await login_po.get_number_code(timeout=timeout)
            if is_success is False:
                return is_success, code_str

            # 5. 输入一层验证码
            is_success, code_input = await login_po.get_login_number_code_input(timeout=timeout)
            if is_success is False:
                return is_success, code_input
            await locator_input_element(locator=code_input, text=code_str.lower())

            # 6. 点击登录
            is_success, login_btn = await login_po.get_login_btn(timeout=timeout)
            if is_success is False:
                return is_success, login_btn
            await on_click_locator(locator=login_btn)
        else:
            # 7. 重复一次全流程的登录
            await _username_login(login_po=login_po, username=username, password=password, timeout=timeout)

        await asyncio.sleep(delay=timeout)

    return True, f"账号:{username} 一次登录流程结束"


async def wechat_login(
        browser: BrowserContext, login_po: LoginPage, timeout: float = 5.0, retry: int = 3
) -> Tuple[bool, str]:
    for index in range(retry):
        # 全流程的登录
        is_success, message = await _wechat_login(browser=browser, login_po=login_po, timeout=timeout)

        # 判断是否为当前页
        if is_success is True or index == retry - 1:
            return is_success, message
