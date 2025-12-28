# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     order_detail_page.py
# Description:  订单详情页面对象
# Author:       ASUS
# CreateDate:   2025/12/16
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Dict, Any, List, Tuple
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo
from qlv_helper.config.url_const import order_detail_url


class OrderDetailPage(BasePo):
    url: str = order_detail_url
    __page: Page

    def __init__(self, page: Page, url: str = order_detail_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_order_lock_state_btn(self, timeout: float = 5.0) -> Tuple[str, Locator]:
        """
        订单详情页面，获取订单锁单状态按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="order_information "]//a[(@class="view_detail_red" and contains(text(), "强制解锁")) or (@class="view_detail_green" and (contains(text(), "锁定") or contains(text(), "解锁返回") or contains(text(), "操作")))]'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        text: str = (await locator.inner_text()).strip()
        return text, locator

    async def get_out_ticket_platform_type_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取出票地类型下拉菜单按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//select[@id="OutTktPFTypeID"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_out_ticket_platform_type_select_option(self, select_option: str, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取出票地类型下拉菜单选项
        :param select_option: 要获取的选项
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//table[@id="PurchaseInfos"]//select[@id="OutTktPFTypeID"]/option[contains(text(), "{select_option}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_out_ticket_platform_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取出票平台下拉菜单按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//select[@id="OutTktPF"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_out_ticket_platform_select_option(self, select_option: str, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取出票平台下拉菜单选项
        :param select_option: 要获取的选项
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//table[@id="PurchaseInfos"]//select[@id="OutTktPF"]/option[contains(text(), "{select_option}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_out_ticket_account_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取出票账号下拉菜单按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//select[@id="AccountNumber"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_out_ticket_account_select_option(self, select_option: str, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取出票账号下拉菜单选项
        :param select_option: 要获取的选项
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//table[@id="PurchaseInfos"]//select[@id="AccountNumber"]/option[contains(text(), "{select_option}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_purchase_account_type_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取采购账号类型下拉菜单按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//select[@id="TypeName"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_purchase_account_type_select_option(self, select_option: str, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取采购账号类型下拉菜单选项
        :param select_option: 要获取的选项
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//table[@id="PurchaseInfos"]//select[@id="TypeName"]/option[contains(text(), "{select_option}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_purchase_account_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取采购账号下拉菜单按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//select[@id="PurchaseAccount"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_purchase_account_select_option(self, select_option: str, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取采购账号下拉菜单选项
        :param select_option: 要获取的选项
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//table[@id="PurchaseInfos"]//select[@id="PurchaseAccount"]/option[contains(text(), "{select_option}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_purchase_amount_input(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取采购金额输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//input[@id="TransactionAmount"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_remark_input(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取备注输入框，一般输入登录官网的"账号/密码"
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//input[@id="Remark"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_main_check_input(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取对账标识输入框，一般输入虚拟卡的card_id
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//input[@id="MainCheckNumber"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_air_comp_order_id_input(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取官网订单号输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//input[@id="AirCoOrderID"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_procurement_info_save_btn(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，采购信息栏，获取【保存采购】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//table[@id="PurchaseInfos"]//input[@id="submit"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_passenger_itinerary_locators(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        """
        订单详情页面，乘客信息栏，获取票号输入框
        :param timeout：超时时间（秒）
        :return: List[{
                    "username": str,
                    "id_number": str,
                    "locator": Locator  # 指向 <input name="ticketNo">
                    }]
        """
        results = list()
        tbody_selector: str = '(//div[@class="order_information"]//table[@class="table table_border table_center"]/tbody)[3]'
        tbody_locator: Locator = await self.get_locator(selector=tbody_selector, timeout=timeout)
        # 只选真正的数据行（有 pid / ticketNo 的 tr）
        rows = tbody_locator.locator("tr[pid]")
        row_count = await rows.count()
        for i in range(row_count):
            row = rows.nth(i)

            out_ticket_state: Locator = await self.get_sub_locator(
                locator=row, selector='xpath=(.//td)[1]', timeout=timeout
            )
            out_ticket_state_text = (await out_ticket_state.inner_text()).strip()
            if "已出票" in out_ticket_state_text:
                continue

            # 1️⃣ 用户名
            name_locator = await self.get_sub_locator(
                locator=row, selector='xpath=.//span[@name="pname"]', timeout=timeout
            )
            username = (await name_locator.first.inner_text()).strip()

            # 2️⃣ 身份证号
            # a 标签里：javascript:showIDNo('身份证号', ...)
            id_link = await self.get_sub_locator(locator=row, selector='xpath=.//a[starts-with(@id, "IDNo_")]',
                                                 timeout=timeout)

            href = await id_link.first.get_attribute("href")
            # href 示例：
            # javascript:showIDNo('320324198511254466','175687',...)

            id_number = None
            if href:
                # 非正则版本，更安全
                start = href.find("'") + 1
                end = href.find("'", start)
                id_number = href[start:end]

            # 3️⃣ ticketNo 输入框 locator
            ticket_input = await self.get_sub_locator(locator=row, selector='xpath=.//input[@name="ticketNo"]',
                                                      timeout=timeout)

            # 防御性校验（可选）
            if await ticket_input.count() == 0:
                continue

            results.append({
                "username": username,
                "id_number": id_number,
                "locator": ticket_input  # Playwright Locator 对象
            })
        return results

    async def get_custom_remark_input(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，日志记录栏，获取自定义备注输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@id="rmk"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_custom_remark_save_btn(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，日志记录栏，获取【保存备注】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//a[@href="javascript:fnSaveRemark()"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_message_notice_dialog_confirm_btn(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，消息提醒弹框，获取【确认】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//a[@id="alertMsg_btnConfirm"]/cite'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_policy_input(self, timeout: float = 5.0) -> Locator:
        """
        订单详情页面，获取政策代码输入框
        :param timeout:
        :return:
        """
        selector: str = '//legend//input[@name="PolicyName"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_purchase_info_transaction_id(self, timeout: float = 5.0) -> List[str]:
        """
        获取订单详情页面的采购信息流水
        :param timeout:
        :return:
        """
        # selector: str = '//tr[@class="PurchaseInfoClass"]'
        selector: str = '//table[@id="PurchaseInfos"]/tbody/tr'
        loc: Locator = await self.get_locator(selector=selector, timeout=timeout)
        locators = await loc.all()
        transaction_ids = list()
        for locator in locators:
            transaction_id = await locator.get_attribute("transactionid")
            if transaction_id:
                transaction_ids.append(transaction_id.strip())
        return transaction_ids
